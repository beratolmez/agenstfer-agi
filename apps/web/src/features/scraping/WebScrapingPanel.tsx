import React, { useState, useEffect } from 'react';

type ScrapeStatus = 'pending' | 'success' | 'error';

interface ScrapeTask {
  id: string;
  url: string;
  status: ScrapeStatus;
  extractedMarkdown?: string;
}

const MOCK_TASKS: ScrapeTask[] = [
  { id: '1', url: 'https://example.com/about', status: 'success', extractedMarkdown: '# About Us\n\nWe are a company focused on...' },
  { id: '2', url: 'https://example.com/pricing', status: 'pending' },
  { id: '3', url: 'https://example.com/docs', status: 'error' },
  { id: '4', url: 'https://example.com/contact', status: 'pending' },
];

const WebScrapingPanel: React.FC = () => {
  const [tasks, setTasks] = useState<ScrapeTask[]>(MOCK_TASKS);
  const [selectedTask, setSelectedTask] = useState<ScrapeTask | null>(MOCK_TASKS[0]);
  const [progress, setProgress] = useState(25);

  // Mock progress and status updates
  useEffect(() => {
    const interval = setInterval(() => {
      setTasks(prev => {
        const newTasks = [...prev];
        const pendingIndex = newTasks.findIndex(t => t.status === 'pending');
        if (pendingIndex !== -1) {
          newTasks[pendingIndex] = {
            ...newTasks[pendingIndex],
            status: 'success',
            extractedMarkdown: `# Extracted Data\n\nContent from ${newTasks[pendingIndex].url}...`
          };
          const completedCount = newTasks.filter(t => t.status !== 'pending').length;
          setProgress((completedCount / newTasks.length) * 100);
        }
        return newTasks;
      });
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: ScrapeStatus) => {
    switch (status) {
      case 'success': return '#10b981';
      case 'error': return '#ef4444';
      case 'pending': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  return (
    <div className="scraping-panel">
      <style>{`
        .scraping-panel {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          background-color: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
          overflow: hidden;
          display: flex;
          flex-direction: column;
          height: 600px;
          max-width: 900px;
          margin: 0 auto;
          color: #111827;
        }
        .scraping-header {
          padding: 20px;
          border-bottom: 1px solid #e5e7eb;
          background-color: #f9fafb;
        }
        .scraping-title {
          margin: 0 0 12px 0;
          font-size: 1.25rem;
          font-weight: 600;
        }
        .progress-container {
          background-color: #e5e7eb;
          border-radius: 9999px;
          height: 8px;
          overflow: hidden;
        }
        .progress-bar {
          background-color: #3b82f6;
          height: 100%;
          transition: width 0.5s ease-in-out;
        }
        .progress-text {
          font-size: 0.875rem;
          color: #6b7280;
          margin-top: 8px;
          text-align: right;
        }
        .scraping-content {
          display: flex;
          flex: 1;
          overflow: hidden;
        }
        .url-list {
          flex: 1;
          border-right: 1px solid #e5e7eb;
          overflow-y: auto;
          padding: 0;
          margin: 0;
          list-style: none;
        }
        .url-item {
          padding: 16px 20px;
          border-bottom: 1px solid #f3f4f6;
          cursor: pointer;
          display: flex;
          justify-content: space-between;
          align-items: center;
          transition: background-color 0.2s;
        }
        .url-item:hover {
          background-color: #f9fafb;
        }
        .url-item.active {
          background-color: #eff6ff;
          border-left: 4px solid #3b82f6;
          padding-left: 16px;
        }
        .url-text {
          font-size: 0.875rem;
          font-weight: 500;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 200px;
        }
        .status-badge {
          font-size: 0.75rem;
          padding: 4px 8px;
          border-radius: 9999px;
          font-weight: 500;
          text-transform: capitalize;
        }
        .preview-pane {
          flex: 2;
          padding: 20px;
          overflow-y: auto;
          background-color: #fafafa;
        }
        .preview-title {
          font-size: 1rem;
          font-weight: 600;
          margin: 0 0 16px 0;
          color: #374151;
        }
        .markdown-preview {
          background-color: #1e1e1e;
          color: #d4d4d4;
          padding: 16px;
          border-radius: 6px;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
          font-size: 0.875rem;
          white-space: pre-wrap;
          line-height: 1.5;
        }
        .empty-preview {
          color: #9ca3af;
          font-style: italic;
          font-size: 0.875rem;
        }
      `}</style>

      <div className="scraping-header">
        <h2 className="scraping-title">Live Web Scraping Status</h2>
        <div className="progress-container">
          <div className="progress-bar" style={{ width: `${progress}%` }}></div>
        </div>
        <div className="progress-text">{Math.round(progress)}% Complete</div>
      </div>

      <div className="scraping-content">
        <ul className="url-list">
          {tasks.map(task => (
            <li 
              key={task.id} 
              className={`url-item ${selectedTask?.id === task.id ? 'active' : ''}`}
              onClick={() => setSelectedTask(task)}
            >
              <span className="url-text" title={task.url}>{task.url}</span>
              <span 
                className="status-badge"
                style={{ 
                  backgroundColor: `${getStatusColor(task.status)}20`,
                  color: getStatusColor(task.status)
                }}
              >
                {task.status}
              </span>
            </li>
          ))}
        </ul>

        <div className="preview-pane">
          <h3 className="preview-title">Extracted Markdown Preview</h3>
          {selectedTask ? (
            selectedTask.extractedMarkdown ? (
              <div className="markdown-preview">
                {selectedTask.extractedMarkdown}
              </div>
            ) : (
              <div className="empty-preview">
                No content extracted yet for this URL. Status: {selectedTask.status}
              </div>
            )
          ) : (
            <div className="empty-preview">Select a URL to view preview</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WebScrapingPanel;
