import { useState, useEffect, useRef } from 'react'
import { supabase } from '../lib/supabase'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import './MedicalChatbot.css'

const WELCOME_MESSAGE =
   "Hello! I'm your Medical Assistant. How can I help you today?"

export default function MedicalChatbot() {
  const [messages, setMessages] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(scrollToBottom, [messages])
  useEffect(() => { initializeChat() }, [])

  const initializeChat = async () => {
    const { data: session } = await supabase
      .from('chat_sessions')
      .insert({ title: 'Medical Consultation' })
      .select()
      .maybeSingle()

    setSessionId(session.id)

    const welcomeMsg = {
      session_id: session.id,
      role: 'assistant',
      content: WELCOME_MESSAGE
    }

    await supabase.from('chat_messages').insert(welcomeMsg)

    setMessages([{ ...welcomeMsg, created_at: new Date().toISOString() }])
  }

  const fetchRagAnswer = async (question) => {
    const res = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: question })
    })

    const data = await res.json()
    return data.answer
  }

  const handleSendMessage = async (content) => {
    if (!sessionId) return
    setIsLoading(true)

    const userMessage = {
      session_id: sessionId,
      role: 'user',
      content
    }

    const { data: userMsg } = await supabase
      .from('chat_messages')
      .insert(userMessage)
      .select()
      .maybeSingle()

    setMessages(prev => [...prev, userMsg])

    try {
      const assistantContent = await fetchRagAnswer(content)

      const assistantMessage = {
        session_id: sessionId,
        role: 'assistant',
        content: assistantContent
      }

      const { data: assistantMsg } = await supabase
        .from('chat_messages')
        .insert(assistantMessage)
        .select()
        .maybeSingle()

      setMessages(prev => [...prev, assistantMsg])
    } catch (err) {
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="medical-chatbot">
      <div className="chat-header">
        <h1>MediCare AI</h1>
        {/* <p>Your AI health companion</p> */}
      </div>

      <div className="chat-messages">
        {messages.map((m) => (
          <ChatMessage
            key={m.id || Math.random()}
            role={m.role}
            content={m.content}
            timestamp={m.created_at}
          />
        ))}

        {isLoading && <div className="typing-indicator">Thinking...</div>}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
    </div>
  )
}
