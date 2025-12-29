import React, { useState, useEffect, useRef } from 'react';
import { Drawer, Input, Button, List, Space, Tag, Avatar, Tooltip, message as antdMessage } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, DeleteOutlined, LinkOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { useAuthStore } from '@/stores/authStore';
import { useNavigate } from 'react-router-dom';
import { tablesApi } from '@/api/endpoints/tables';

interface ActionItem {
  id: string;
  type: 'focus_node' | 'trace_path';
  label: string;
  payload: any;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  type: 'text' | 'table' | 'action_card' | 'status';
  actions?: ActionItem[]; // Store available actions for this message
  timestamp: number;
}

interface ChatSidebarProps {
  open: boolean;
  onClose: () => void;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({ open, onClose }) => {
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am Ariadne AI. How can I help you with your data lineage today?',
      type: 'text',
      timestamp: Date.now(),
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [tableMap, setTableMap] = useState<Map<string, string>>(new Map());
  const scrollRef = useRef<HTMLDivElement>(null);
  const { token } = useAuthStore.getState();

  // Load table names for label resolution
  useEffect(() => {
    if (open) {
        tablesApi.list({ size: 1000 }).then(res => {
            const map = new Map<string, string>();
            res.items.forEach((t: any) => map.set(t.id, t.name));
            setTableMap(map);
        }).catch(() => {});
    }
  }, [open]);

  // Action Runner: Execute payloads from clicking labels
  const runAction = (actionId: string, msg: Message) => {
    console.log('[AI Chat] Running action:', actionId, 'Available actions:', msg.actions);
    const action = msg.actions?.find(a => a.id === actionId);
    
    if (!action) {
        console.warn('[AI Chat] Action ID not found in registry:', actionId);
        antdMessage.warning(`Action "${actionId}" is unavailable`);
        return;
    }

    if (action.type === 'focus_node') {
        const { id, direction } = action.payload;
        // Deep link navigation
        const query = new URLSearchParams();
        query.set('focus', id);
        if (direction) query.set('direction', direction);
        
        navigate(`/lineage/${id}?${query.toString()}`);
        antdMessage.success(`Focusing on ${tableMap.get(id) || action.label}`);
    } else if (action.type === 'trace_path') {
        // Future implementation for path tracing
        const { nodes: pathNodes } = action.payload;
        if (pathNodes && pathNodes.length > 0) {
            const firstId = pathNodes[0].id;
            navigate(`/lineage/${firstId}?focus=${firstId}`);
        }
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      type: 'text',
      timestamp: Date.now(),
    };

    const prompt = input;
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setStatusMsg('Connecting to Ariadne Intelligence...');

    const assistantMsgId = (Date.now() + 1).toString();
    
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
      const url = `${baseUrl}/ai/chat`;
      
      await fetchEventSource(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: prompt,
          conversation_id: conversationId,
        }),
        onopen: async (response) => {
          if (response.status === 401) {
            const { useAuthStore } = await import('@/stores/authStore');
            useAuthStore.getState().logout();
            window.location.href = '/login';
            throw new Error('Unauthorized');
          }
        },
        onmessage: (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log(`[AI Chat] Event: ${event.event}`, data);
            
            if (event.event === 'status') {
              setStatusMsg(data.message);
            } else if (event.event === 'data') {
              setMessages(prev => {
                const existing = prev.find(m => m.id === assistantMsgId);
                
                // Content sanitization: Remove any leaked JSON action blocks
                const sanitize = (text: string) => {
                    return text.replace(/<actions>[\s\S]*?<\/actions>/g, '').trim();
                };

                if (existing) {
                  return prev.map(m => m.id === assistantMsgId 
                    ? { 
                        ...m, 
                        content: data.type === 'text' ? sanitize(m.content + data.content) : m.content,
                        actions: data.type === 'actions' ? data.content : m.actions
                      } 
                    : m
                  );
                } else {
                  return [...prev, {
                    id: assistantMsgId,
                    role: 'assistant',
                    content: data.type === 'text' ? sanitize(data.content) : '',
                    type: data.type,
                    actions: data.type === 'actions' ? data.content : [],
                    timestamp: Date.now(),
                  }];
                }
              });
              
              if (data.conversation_id) setConversationId(data.conversation_id);
            }
          } catch (e) { console.error('[AI Chat] Parsing Error:', e); }
        },
        onclose: () => { setLoading(false); setStatusMsg(null); },
        onerror: (err) => { setLoading(false); setStatusMsg(null); throw err; }
      });
    } catch (error: any) {
      setLoading(false);
      setStatusMsg(null);
    }
  };

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, statusMsg]);

  // Custom Markdown renderer to handle standard [Label](action:ID)
  const renderMessageContent = (msg: Message) => {
    return (
      <ReactMarkdown
        components={{
          // Intercept 'a' tags to handle our custom 'action:' protocol
          a: ({ href, children }) => {
            if (href?.startsWith('action:')) {
              const actionId = href.replace('action:', '');
              return (
                <Tag 
                  color="blue" 
                  icon={<LinkOutlined />}
                  style={{ cursor: 'pointer', margin: '0 2px', fontWeight: '500' }}
                  onClick={(e) => {
                      e.preventDefault();
                      runAction(actionId, msg);
                  }}
                >
                  {children}
                </Tag>
              );
            }
            // Render standard external links safely
            return <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>;
          }
        }}
      >
        {msg.content}
      </ReactMarkdown>
    );
  };

  return (
    <Drawer
      title={
        <Space>
          <RobotOutlined style={{ color: '#1890ff' }} />
          <span>Ariadne AI Assistant</span>
        </Space>
      }
      placement="right"
      width={450}
      onClose={onClose}
      open={open}
      mask={false}
      extra={
        <Space>
          <Tooltip title="Clear History">
            <Button type="text" icon={<DeleteOutlined />} onClick={() => { setMessages([]); setConversationId(null); }} />
          </Tooltip>
        </Space>
      }
      styles={{ body: { padding: 0, display: 'flex', flexDirection: 'column' } }}
    >
      <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', padding: '20px 16px', background: '#f9fafb' }}>
        <List
          dataSource={messages}
          renderItem={(msg) => (
            <div style={{ marginBottom: 20, display: 'flex', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}>
              <Avatar 
                icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />} 
                style={{ backgroundColor: msg.role === 'user' ? '#1890ff' : '#52c41a', flexShrink: 0 }} 
              />
              <div style={{ 
                maxWidth: '85%', 
                margin: msg.role === 'user' ? '0 12px 0 0' : '0 0 0 12px',
                padding: '10px 14px',
                borderRadius: 12,
                backgroundColor: msg.role === 'user' ? '#1890ff' : '#fff',
                color: msg.role === 'user' ? '#fff' : 'inherit',
                boxShadow: '0 2px 6px rgba(0,0,0,0.05)',
                position: 'relative'
              }}>
                <div className="markdown-content">
                  {renderMessageContent(msg)}
                </div>
                
                {/* Action Bar (Fallback if not embedded inline) */}
                {msg.role === 'assistant' && msg.actions && msg.actions.length > 0 && (
                  <div style={{ marginTop: 12, borderTop: '1px solid #f0f0f0', paddingTop: 8 }}>
                    <Space wrap size={[4, 8]}>
                      {msg.actions.map(action => (
                        <Button 
                          key={action.id} 
                          size="small" 
                          icon={<LinkOutlined />} 
                          onClick={() => runAction(action.id, msg)}
                        >
                          {action.label}
                        </Button>
                      ))}
                    </Space>
                  </div>
                )}

                <div style={{ fontSize: '10px', opacity: 0.5, marginTop: 4, textAlign: msg.role === 'user' ? 'right' : 'left' }}>
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          )}
        />
        {loading && statusMsg && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginLeft: 4, marginBottom: 16 }}>
            <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
            <Tag color="processing">{statusMsg}</Tag>
          </div>
        )}
      </div>

      <div style={{ padding: '16px', borderTop: '1px solid #f0f0f0', background: '#fff' }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input placeholder="Ask about data lineage or paste SQL..." value={input} onChange={(e) => setInput(e.target.value)} onPressEnter={handleSend} disabled={loading} />
          <Button type="primary" icon={<SendOutlined />} onClick={handleSend} loading={loading} />
        </Space.Compact>
      </div>
    </Drawer>
  );
};

export default ChatSidebar;
