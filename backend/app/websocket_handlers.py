from flask_socketio import emit, join_room, leave_room
from flask import session, request
from . import socketio, db
from .models import User, Pipeline, PipelineExecution
from .services.bitbucket_service import BitbucketService
import threading
import time


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f'Client connected: {request.sid}')
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print(f'Client disconnected: {request.sid}')


@socketio.on('subscribe_logs')
def handle_subscribe_logs(data):
    """Subscribe to real-time logs for a pipeline execution"""
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'message': 'Not authenticated'})
        return
    
    pipeline_id = data.get('pipeline_id')
    execution_id = data.get('execution_id')
    
    if not pipeline_id:
        emit('error', {'message': 'pipeline_id is required'})
        return
    
    # Verify user has access to this pipeline
    user = User.query.get(user_id)
    pipeline = Pipeline.query.get(pipeline_id)
    
    if not pipeline or pipeline.repository.user_id != user.id:
        emit('error', {'message': 'Pipeline not found'})
        return
    
    # Join room for this pipeline
    room = f'pipeline_{pipeline_id}'
    join_room(room)
    
    emit('subscribed', {
        'pipeline_id': pipeline_id,
        'execution_id': execution_id,
        'room': room
    })
    
    # Start streaming logs if execution is in progress
    if execution_id:
        execution = PipelineExecution.query.get(execution_id)
        if execution and execution.status in ['BUILDING', 'TESTING', 'DEPLOYING']:
            # Start background task to stream logs
            thread = threading.Thread(
                target=stream_pipeline_logs,
                args=(user.bitbucket_token, pipeline, execution, room)
            )
            thread.daemon = True
            thread.start()


@socketio.on('unsubscribe_logs')
def handle_unsubscribe_logs(data):
    """Unsubscribe from pipeline logs"""
    pipeline_id = data.get('pipeline_id')
    if pipeline_id:
        room = f'pipeline_{pipeline_id}'
        leave_room(room)
        emit('unsubscribed', {'pipeline_id': pipeline_id})


def stream_pipeline_logs(bitbucket_token, pipeline, execution, room):
    """
    Stream logs in real-time from Bitbucket (background task)
    
    Emits two event types:
    - 'pipeline_logs': Real-time log updates from pipeline execution
    - 'pipeline_status': Status change notifications (BUILDING, TESTING, DEPLOYING, SUCCESS, FAILED)
    """
    if not bitbucket_token or not execution.bitbucket_pipeline_uuid:
        return
    
    bitbucket_service = BitbucketService(bitbucket_token)
    repository = pipeline.repository
    
    last_status = execution.status
    last_step_states = {}
    max_iterations = 120  # Max 10 minutes (120 * 5 seconds)
    iteration = 0
    
    while iteration < max_iterations:
        try:
            # Get current logs
            logs_data = bitbucket_service.get_pipeline_logs(
                workspace=repository.bitbucket_workspace,
                repo_slug=repository.name,
                pipeline_uuid=execution.bitbucket_pipeline_uuid
            )
            
            current_status = logs_data['state']
            
            # Emit status change if status changed
            if current_status != last_status:
                socketio.emit('pipeline_status', {
                    'pipeline_id': pipeline.id,
                    'execution_id': execution.id,
                    'status': current_status,
                    'previous_status': last_status,
                    'timestamp': time.time()
                }, room=room)
                
                last_status = current_status
                
                # Update database
                execution.status = current_status
                if current_status in ['COMPLETED', 'FAILED', 'STOPPED', 'ERROR']:
                    execution.completed_at = time.strftime('%Y-%m-%d %H:%M:%S')
                    if logs_data.get('duration_in_seconds'):
                        execution.duration_seconds = logs_data['duration_in_seconds']
                
                db.session.commit()
            
            # Prepare step logs with change detection
            steps_with_changes = []
            for step in logs_data['steps']:
                step_name = step['name']
                step_state = step['state']
                
                # Check if this step has new logs or state change
                if step_name not in last_step_states or last_step_states[step_name] != step_state:
                    steps_with_changes.append({
                        'name': step_name,
                        'state': step_state,
                        'duration_seconds': step.get('duration_in_seconds'),
                        'log_preview': step['log'][:1000] if step['log'] else None,  # First 1000 chars
                        'log_full': step['log'],  # Full log
                        'has_log': bool(step['log']),
                        'started_on': step.get('started_on'),
                        'completed_on': step.get('completed_on'),
                        'is_new': step_name not in last_step_states,
                        'state_changed': last_step_states.get(step_name) != step_state
                    })
                    last_step_states[step_name] = step_state
            
            # Emit log update with only changed steps
            if steps_with_changes or iteration == 0:
                socketio.emit('pipeline_logs', {
                    'pipeline_id': pipeline.id,
                    'execution_id': execution.id,
                    'build_number': logs_data['build_number'],
                    'status': current_status,
                    'steps': steps_with_changes,
                    'total_steps': len(logs_data['steps']),
                    'duration_seconds': logs_data.get('duration_in_seconds'),
                    'timestamp': time.time()
                }, room=room)
            
            # Check if pipeline is complete
            if current_status in ['COMPLETED', 'FAILED', 'STOPPED', 'ERROR']:
                # Map Bitbucket status to our internal status
                final_status = 'SUCCESS' if current_status == 'COMPLETED' else 'FAILED'
                
                # Send final update
                socketio.emit('pipeline_status', {
                    'pipeline_id': pipeline.id,
                    'execution_id': execution.id,
                    'status': final_status,
                    'bitbucket_status': current_status,
                    'duration_seconds': logs_data.get('duration_in_seconds'),
                    'completed_at': logs_data.get('completed_on'),
                    'final': True,
                    'timestamp': time.time()
                }, room=room)
                
                # Store final logs in database
                full_log = '\n\n'.join([
                    f"=== {step['name']} ===\nStatus: {step['state']}\nDuration: {step.get('duration_in_seconds', 0)}s\n{step['log'] or 'No log available'}"
                    for step in logs_data['steps']
                ])
                execution.logs = full_log
                execution.status = final_status
                
                # Update pipeline status
                pipeline.status = final_status
                
                db.session.commit()
                
                break
            
            iteration += 1
            time.sleep(5)  # Poll every 5 seconds
            
        except Exception as e:
            socketio.emit('log_error', {
                'pipeline_id': pipeline.id,
                'execution_id': execution.id,
                'error': str(e),
                'timestamp': time.time()
            }, room=room)
            
            # Store error in database
            execution.error_message = str(e)
            execution.status = 'FAILED'
            db.session.commit()
            
            break
    
    # Timeout reached
    if iteration >= max_iterations:
        socketio.emit('log_timeout', {
            'pipeline_id': pipeline.id,
            'execution_id': execution.id,
            'message': 'Log streaming timeout reached',
            'timestamp': time.time()
        }, room=room)


@socketio.on('get_execution_status')
def handle_get_execution_status(data):
    """Get current status of a pipeline execution"""
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'message': 'Not authenticated'})
        return
    
    execution_id = data.get('execution_id')
    if not execution_id:
        emit('error', {'message': 'execution_id is required'})
        return
    
    execution = PipelineExecution.query.get(execution_id)
    if not execution:
        emit('error', {'message': 'Execution not found'})
        return
    
    # Verify user has access
    user = User.query.get(user_id)
    if execution.pipeline.repository.user_id != user.id:
        emit('error', {'message': 'Access denied'})
        return
    
    emit('execution_status', {
        'execution_id': execution.id,
        'pipeline_id': execution.pipeline_id,
        'status': execution.status,
        'build_number': execution.bitbucket_build_number,
        'started_at': execution.started_at.isoformat() if execution.started_at else None,
        'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
        'duration_seconds': execution.duration_seconds,
        'trigger_type': execution.trigger_type
    })


@socketio.on('subscribe_pipeline_status')
def handle_subscribe_pipeline_status(data):
    """Subscribe to status updates for a specific pipeline"""
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'message': 'Not authenticated'})
        return
    
    pipeline_id = data.get('pipeline_id')
    if not pipeline_id:
        emit('error', {'message': 'pipeline_id is required'})
        return
    
    # Verify access
    user = User.query.get(user_id)
    pipeline = Pipeline.query.get(pipeline_id)
    
    if not pipeline or pipeline.repository.user_id != user.id:
        emit('error', {'message': 'Pipeline not found'})
        return
    
    # Join status room
    room = f'pipeline_status_{pipeline_id}'
    join_room(room)
    
    emit('subscribed_status', {
        'pipeline_id': pipeline_id,
        'current_status': pipeline.status
    })

