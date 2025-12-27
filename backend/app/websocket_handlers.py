from flask_socketio import emit, join_room, leave_room
from flask import session, request
from . import socketio
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
    """Stream logs in real-time from Bitbucket (background task)"""
    if not bitbucket_token or not execution.bitbucket_pipeline_uuid:
        return
    
    bitbucket_service = BitbucketService(bitbucket_token)
    repository = pipeline.repository
    
    last_log_length = 0
    max_iterations = 60  # Max 5 minutes (60 * 5 seconds)
    iteration = 0
    
    while iteration < max_iterations:
        try:
            # Get current logs
            logs_data = bitbucket_service.get_pipeline_logs(
                workspace=repository.bitbucket_workspace,
                repo_slug=repository.name,
                pipeline_uuid=execution.bitbucket_pipeline_uuid
            )
            
            # Emit status update
            socketio.emit('log_update', {
                'pipeline_id': pipeline.id,
                'execution_id': execution.id,
                'status': logs_data['state'],
                'steps': [{
                    'name': step['name'],
                    'state': step['state'],
                    'duration_seconds': step.get('duration_in_seconds'),
                    'log_preview': step['log'][:500] if step['log'] else None
                } for step in logs_data['steps']]
            }, room=room)
            
            # Check if pipeline is complete
            if logs_data['state'] in ['COMPLETED', 'FAILED', 'STOPPED', 'ERROR']:
                # Send final update
                socketio.emit('log_complete', {
                    'pipeline_id': pipeline.id,
                    'execution_id': execution.id,
                    'status': logs_data['state'],
                    'duration_seconds': logs_data.get('duration_in_seconds')
                }, room=room)
                break
            
            iteration += 1
            time.sleep(5)  # Poll every 5 seconds
            
        except Exception as e:
            socketio.emit('log_error', {
                'pipeline_id': pipeline.id,
                'execution_id': execution.id,
                'error': str(e)
            }, room=room)
            break
