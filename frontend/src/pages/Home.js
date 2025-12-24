import React from 'react';
import { Link } from 'react-router-dom';

function Home() {
  return (
    <div>
      <div className="hero">
        <h1>DevOps Tool</h1>
        <p>Automate Bitbucket Pipeline Creation and Testing</p>
        <Link to="/dashboard">
          <button className="button" style={{ fontSize: '1.25rem', padding: '1rem 2rem' }}>
            Get Started
          </button>
        </Link>
      </div>
      
      <div className="container">
        <div className="features">
          <div className="feature">
            <h3>🔗 OAuth Integration</h3>
            <p>Connect your Bitbucket and GitHub accounts seamlessly with OAuth authentication.</p>
          </div>
          
          <div className="feature">
            <h3>📦 Repository Management</h3>
            <p>Select repositories from GitHub or Bitbucket and automatically migrate them.</p>
          </div>
          
          <div className="feature">
            <h3>🤖 AI-Powered Pipelines</h3>
            <p>Use Gemini 3 Pro to generate and iteratively fix pipeline configurations.</p>
          </div>
          
          <div className="feature">
            <h3>🧪 Self-Hosted Testing</h3>
            <p>Test pipelines in an integrated runner before deploying to production.</p>
          </div>
          
          <div className="feature">
            <h3>🚀 Automated Pull Requests</h3>
            <p>Automatically create PRs with working pipeline configurations.</p>
          </div>
          
          <div className="feature">
            <h3>🌐 Domain Management</h3>
            <p>Configure root domains and subdomains for your tools and features.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
