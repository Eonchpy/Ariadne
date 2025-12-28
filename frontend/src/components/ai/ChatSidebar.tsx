import React, { useState, useEffect, useRef } from 'react';
import { Drawer, Input, Button, List, Typography, Space, Tag, Avatar, Tooltip, message as antdMessage } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, DeleteOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { useAuthStore } from '@/stores/authStore';

const { Text } = Typography;

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  type: 'text' | 'table' | 'action_card' | 'status';
  timestamp: number;
}

interface ChatSidebarProps {
  open: boolean;
  onClose: () => void;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({ open, onClose }) => {
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
  const scrollRef = useRef<HTMLDivElement>(null);
  const { token } = useAuthStore.getState();

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
      
      console.log(`[AI Chat] Attempting connection to: ${url}`);
      console.log(`[AI Chat] Token present: ${!!token}`);

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
          console.log(`[AI Chat] Connection opened. Status: ${response.status}`);
          
          if (response.status === 401) {
            console.error('[AI Chat] Authentication expired (401)');
            antdMessage.error('Session expired. Please log in again.');
            const { useAuthStore } = await import('@/stores/authStore');
            useAuthStore.getState().logout();
            window.location.href = '/login';
            throw new Error('Unauthorized');
          }

          if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            console.error('[AI Chat] Connection failed:', errData);
            throw new Error(`Server returned ${response.status}: ${JSON.stringify(errData)}`);
          }
        },
        onmessage: (event) => {
          console.log(`[AI Chat] Message received. Event: ${event.event}`, event.data);
          try {
            const data = JSON.parse(event.data);
            
            if (event.event === 'status') {
              setStatusMsg(data.message);
            } else if (event.event === 'data') {
              setMessages(prev => {
                const existing = prev.find(m => m.id === assistantMsgId);
                if (existing) {
                  return prev.map(m => m.id === assistantMsgId 
                    ? { ...m, content: m.content + (data.type === 'text' ? data.content : '') } 
                    : m
                  );
                } else {
                  return [...prev, {
                    id: assistantMsgId,
                    role: 'assistant',
                    content: data.type === 'text' ? data.content : '',
                    type: data.type,
                    timestamp: Date.now(),
                  }];
                }
              });
              
              if (data.conversation_id) {
                setConversationId(data.conversation_id);
              }
            }
          } catch (e) {
            console.error('[AI Chat] Failed to parse message data:', e);
          }
        },
        onclose: () => {
          console.log('[AI Chat] Connection closed by server');
          setLoading(false);
          setStatusMsg(null);
        },
        onerror: (err) => {
          console.error('[AI Chat] SSE Streaming Error:', err);
          setLoading(false);
          setStatusMsg(null);
          antdMessage.error(`Connection error: ${err.message || 'Check console'}`);
          throw err; // Stop retrying
        }
      });
    } catch (error: any) {
      console.error('[AI Chat] Outer Catch Error:', error);
      setLoading(false);
      setStatusMsg(null);
      antdMessage.error(`Failed to start chat: ${error.message}`);
    }
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, statusMsg]);

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
            <Button type="text" icon={<DeleteOutlined />} onClick={() => {
                setMessages([]);
                setConversationId(null);
            }} />
          </Tooltip>
        </Space>
      }
      styles={{ body: { padding: 0, display: 'flex', flexDirection: 'column' } }}
    >
      {/* Message Area */}
      <div 
        ref={scrollRef}
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '20px 16px',
          background: '#f9fafb' 
        }}
      >
        <List
          dataSource={messages}
          renderItem={(msg) => (
            <div style={{ 
              marginBottom: 20, 
              display: 'flex', 
              flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' 
            }}>
              <Avatar 
                icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />} 
                style={{ 
                  backgroundColor: msg.role === 'user' ? '#1890ff' : '#52c41a',
                  flexShrink: 0
                }} 
              />
              <div style={{ 
                maxWidth: '80%', 
                margin: msg.role === 'user' ? '0 12px 0 0' : '0 0 0 12px',
                padding: '10px 14px',
                borderRadius: 12,
                backgroundColor: msg.role === 'user' ? '#1890ff' : '#fff',
                color: msg.role === 'user' ? '#fff' : 'inherit',
                boxShadow: '0 2px 6px rgba(0,0,0,0.05)',
                position: 'relative'
              }}>
                <div className="markdown-content">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
                <div style={{ 
                  fontSize: '10px', 
                  opacity: 0.5, 
                  marginTop: 4, 
                  textAlign: msg.role === 'user' ? 'right' : 'left' 
                }}>
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

      {/* Input Area */}
      <div style={{ padding: '16px', borderTop: '1px solid #f0f0f0', background: '#fff' }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input 
            placeholder="Ask about data lineage or paste SQL..." 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={handleSend}
            disabled={loading}
          />
          <Button type="primary" icon={<SendOutlined />} onClick={handleSend} loading={loading} />
        </Space.Compact>
        <div style={{ marginTop: 8, textAlign: 'center' }}>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            Tip: Paste SQL to automatically generate lineage relationships.
          </Text>
        </div>
      </div>
    </Drawer>
  );
};

export default ChatSidebar;
