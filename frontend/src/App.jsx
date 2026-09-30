import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const QUICK_PROMPTS = [
  {
    icon: "📚",
    title: "AIML Syllabus",
    subtitle: "Explore subjects and curriculum",
    message: "What is the AIML syllabus?",
  },
  {
    icon: "📅",
    title: "Academic Calendar",
    subtitle: "Important dates and events",
    message: "What is the academic calendar?",
  },
  {
    icon: "₹",
    title: "College Fees",
    subtitle: "Fee structure and payments",
    message: "What is the college fee structure?",
  },
  {
    icon: "💼",
    title: "Placements",
    subtitle: "Placement information",
    message: "Tell me about college placements.",
  },
];

const DEFAULT_USER = {
  user_id: "default_student_user",
  name: "Student",
  email: "student@college.edu",
  role: "student",
};

function App() {
  const [user, setUser] = useState(DEFAULT_USER);

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);

  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);

  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState(true);
  const [mobileSidebar, setMobileSidebar] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  /* -------------------------------------------------------
     AUTO INITIALIZE USER
  ------------------------------------------------------- */

  useEffect(() => {
    async function initUser() {
      // Check backend health
      try {
        const healthRes = await fetch(`${API_BASE}/health`);
        if (healthRes.ok) {
          setBackendOnline(true);
        }
      } catch {
        // Fallback check on root health
        try {
          const healthRes = await fetch("http://localhost:8000/api/health");
          if (healthRes.ok) setBackendOnline(true);
        } catch {
          setBackendOnline(false);
        }
      }

      const savedUser = localStorage.getItem("college_ai_user");
      if (savedUser) {
        try {
          setUser(JSON.parse(savedUser));
          return;
        } catch {
          localStorage.removeItem("college_ai_user");
        }
      }

      // Automatically register/retrieve default student user from backend
      try {
        const response = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            name: "Student",
            email: "student@college.edu",
          }),
        });

        if (response.ok) {
          const data = await response.json();
          setUser(data);
          localStorage.setItem("college_ai_user", JSON.stringify(data));
          setBackendOnline(true);
        }
      } catch (error) {
        console.error("Auto login error:", error);
      }
    }

    initUser();
  }, []);

  /* -------------------------------------------------------
     LOAD CONVERSATIONS
  ------------------------------------------------------- */

  useEffect(() => {
    if (!user?.user_id) return;

    loadConversations();
  }, [user]);

  /* -------------------------------------------------------
     AUTO SCROLL
  ------------------------------------------------------- */

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [messages, loading]);

  /* -------------------------------------------------------
     LOAD USER CONVERSATIONS
  ------------------------------------------------------- */

  async function loadConversations() {
    try {
      const response = await fetch(
        `${API_BASE}/conversations?user_id=${encodeURIComponent(user.user_id)}`,
        {
          headers: {
            Accept: "application/json",
          },
        }
      );

      if (!response.ok) {
        return;
      }

      const data = await response.json();

      if (Array.isArray(data)) {
        setConversations(data);
      } else if (Array.isArray(data?.conversations)) {
        setConversations(data.conversations);
      }
    } catch (error) {
      console.log("Conversation loading skipped:", error);
    }
  }

  /* -------------------------------------------------------
     LOAD EXISTING CONVERSATION
  ------------------------------------------------------- */

  async function openConversation(id) {
    if (!id) return;

    try {
      setLoading(true);

      const response = await fetch(
        `${API_BASE}/conversations/${encodeURIComponent(id)}`,
        {
          headers: {
            Accept: "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error("Could not load conversation");
      }

      const data = await response.json();

      setConversationId(id);

      const loadedMessages =
        data?.messages ||
        data?.conversation?.messages ||
        [];

      if (Array.isArray(loadedMessages)) {
        setMessages(loadedMessages);
      }

      setMobileSidebar(false);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  /* -------------------------------------------------------
     NEW CONVERSATION
  ------------------------------------------------------- */

  function startNewConversation() {
    setConversationId(null);
    setMessages([]);
    setMessage("");
    setMobileSidebar(false);

    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  }

  /* -------------------------------------------------------
     SEND CHAT MESSAGE
  ------------------------------------------------------- */

  async function sendMessage(textOverride = null) {
    const text = (textOverride ?? message).trim();

    if (!text || loading || !user?.user_id) return;

    const userMessage = {
      message_id: `local-${Date.now()}`,
      role: "user",
      content: text,
      sources: [],
    };

    setMessages((previous) => [...previous, userMessage]);
    setMessage("");
    setLoading(true);
    setBackendOnline(true);

    try {
      const payload = {
        user_id: user.user_id,
        message: text,
      };

      if (conversationId) {
        payload.conversation_id = conversationId;
      }

      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || "Chat request failed");
      }

      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      if (data.assistant_message) {
        setMessages((previous) => [
          ...previous,
          data.assistant_message,
        ]);
      }

      if (data.conversation_id) {
        loadConversations();
      }
    } catch (error) {
      console.error("Chat error:", error);

      setBackendOnline(false);

      setMessages((previous) => [
        ...previous,
        {
          message_id: `error-${Date.now()}`,
          role: "assistant",
          content:
            "I couldn't connect to the College AI backend. Please make sure the FastAPI server is running on port 8000.",
          sources: [],
          error: true,
        },
      ]);
    } finally {
      setLoading(false);

      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }

  /* -------------------------------------------------------
     ENTER KEY
  ------------------------------------------------------- */

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  /* -------------------------------------------------------
     FORMAT TIME
  ------------------------------------------------------- */

  function formatTime(dateValue) {
    if (!dateValue) return "";

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) return "";

    return date.toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
    });
  }

  /* -------------------------------------------------------
     CONVERSATION TITLE
  ------------------------------------------------------- */

  function getConversationTitle(conversation) {
    return (
      conversation?.title ||
      conversation?.name ||
      conversation?.last_message ||
      "New conversation"
    );
  }

  /* -------------------------------------------------------
     SOURCE CARD
  ------------------------------------------------------- */

  function SourceCard({ source }) {
    const filename =
      source?.document_filename ||
      source?.filename ||
      "College document";

    const category = source?.category || "College Knowledge Base";

    const page =
      source?.page_number !== undefined
        ? `Page ${source.page_number}`
        : "";

    return (
      <div className="source-card">
        <div className="source-icon">📄</div>

        <div className="source-info">
          <div className="source-name">{filename}</div>

          <div className="source-meta">
            {category}
            {page ? ` • ${page}` : ""}
          </div>
        </div>
      </div>
    );
  }

  /* -------------------------------------------------------
     MESSAGE SOURCES
  ------------------------------------------------------- */

  function Sources({ sources }) {
    if (!Array.isArray(sources) || sources.length === 0) {
      return null;
    }

    const uniqueSources = sources.filter(
      (source, index, array) => {
        const key = `${source?.document_filename}-${source?.page_number}`;

        return (
          index ===
          array.findIndex(
            (item) =>
              `${item?.document_filename}-${item?.page_number}` ===
              key
          )
        );
      }
    );

    return (
      <div className="sources-section">
        <div className="sources-heading">
          <span>🔗</span>
          <span>Sources</span>
        </div>

        <div className="sources-list">
          {uniqueSources.map((source, index) => (
            <SourceCard
              key={`${source?.document_filename}-${source?.page_number}-${index}`}
              source={source}
            />
          ))}
        </div>
      </div>
    );
  }

  /* -------------------------------------------------------
     MARKDOWN RENDERER
  ------------------------------------------------------- */

  function MarkdownAnswer({ content }) {
    return (
      <div className="markdown-content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            table({ children }) {
              return (
                <div className="table-wrapper">
                  <table>{children}</table>
                </div>
              );
            },

            a({ children, ...props }) {
              return (
                <a
                  {...props}
                  target="_blank"
                  rel="noreferrer"
                >
                  {children}
                </a>
              );
            },

            code({ inline, children, ...props }) {
              if (inline) {
                return <code {...props}>{children}</code>;
              }

              return (
                <pre>
                  <code {...props}>{children}</code>
                </pre>
              );
            },
          }}
        >
          {content || ""}
        </ReactMarkdown>
      </div>
    );
  }

  /* -------------------------------------------------------
     WELCOME SCREEN
  ------------------------------------------------------- */

  function WelcomeScreen() {
    return (
      <div className="welcome-screen">
        <div className="welcome-icon">✦</div>

        <h1>Hello, {user?.name || "Student"}!</h1>

        <p>
          What would you like to know about your college?
        </p>

        <div className="quick-grid">
          {QUICK_PROMPTS.map((item) => (
            <button
              className="quick-card"
              key={item.title}
              onClick={() => sendMessage(item.message)}
            >
              <div className="quick-icon">{item.icon}</div>

              <div className="quick-text">
                <strong>{item.title}</strong>
                <span>{item.subtitle}</span>
              </div>

              <span className="quick-arrow">→</span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  /* -------------------------------------------------------
     MAIN APPLICATION
  ------------------------------------------------------- */

  return (
    <div className="app-shell">
      {/* MOBILE OVERLAY */}

      {mobileSidebar && (
        <div
          className="mobile-overlay"
          onClick={() => setMobileSidebar(false)}
        />
      )}

      {/* SIDEBAR */}

      <aside
        className={`sidebar ${mobileSidebar ? "sidebar-open" : ""
          }`}
      >
        <div className="sidebar-top">
          <div className="brand">
            <div className="brand-logo">🎓</div>

            <div>
              <h2>College AI</h2>
              <span>Knowledge Base</span>
            </div>
          </div>

          <button
            className="new-chat-button"
            onClick={startNewConversation}
          >
            <span>＋</span>
            New Conversation
          </button>

          <div className="recent-heading">
            Recent Conversations
          </div>

          <div className="conversation-list">
            {conversations.length === 0 ? (
              <div className="empty-conversations">
                <div>💬</div>
                <span>No previous conversations</span>
              </div>
            ) : (
              conversations.map((conversation, index) => {
                const id =
                  conversation.conversation_id ||
                  conversation.id;

                return (
                  <button
                    key={id || index}
                    className={`conversation-item ${conversationId === id
                        ? "active"
                        : ""
                      }`}
                    onClick={() =>
                      openConversation(id)
                    }
                  >
                    <span className="conversation-icon">
                      💬
                    </span>

                    <span className="conversation-title">
                      {getConversationTitle(
                        conversation
                      )}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="profile">
            <div className="avatar">
              {(user?.name || "S")
                .charAt(0)
                .toUpperCase()}
            </div>

            <div className="profile-info">
              <strong>{user?.name || "Student"}</strong>
              <span>{user?.email || "student@college.edu"}</span>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN AREA */}

      <main className="main-area">
        {/* HEADER */}

        <header className="topbar">
          <div className="header-left">
            <button
              className="mobile-menu"
              onClick={() =>
                setMobileSidebar(true)
              }
              aria-label="Open menu"
            >
              ☰
            </button>

            <div>
              <h1>College AI Assistant</h1>

              <p>
                Ask anything about your college
                documents
              </p>
            </div>
          </div>

          <div
            className={`status ${backendOnline ? "online" : "offline"
              }`}
          >
            <span className="status-dot" />

            {backendOnline
              ? "AI Online"
              : "Backend Offline"}
          </div>
        </header>

        {/* CHAT AREA */}

        <section className="chat-area">
          {messages.length === 0 ? (
            <WelcomeScreen />
          ) : (
            <div className="messages-container">
              {messages.map((item, index) => {
                const isUser =
                  item.role === "user";

                return (
                  <div
                    key={
                      item.message_id ||
                      `${item.role}-${index}`
                    }
                    className={`message-row ${isUser
                        ? "user-row"
                        : "assistant-row"
                      }`}
                  >
                    {!isUser && (
                      <div className="assistant-avatar">
                        ✦
                      </div>
                    )}

                    <div
                      className={`message-content ${isUser
                          ? "user-message"
                          : "assistant-message"
                        } ${item.error ? "error-message" : ""
                        }`}
                    >
                      {isUser ? (
                        <p>{item.content}</p>
                      ) : (
                        <MarkdownAnswer
                          content={item.content}
                        />
                      )}

                      {!isUser && (
                        <Sources
                          sources={item.sources}
                        />
                      )}

                      <span className="message-time">
                        {formatTime(item.created_at)}
                      </span>
                    </div>

                    {isUser && (
                      <div className="user-avatar">
                        {(user.name || "T")
                          .charAt(0)
                          .toUpperCase()}
                      </div>
                    )}
                  </div>
                );
              })}

              {loading && (
                <div className="message-row assistant-row">
                  <div className="assistant-avatar">
                    ✦
                  </div>

                  <div className="typing-bubble">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </section>

        {/* INPUT AREA */}

        <footer className="composer-area">
          <div className="composer">
            <div className="composer-icon">✦</div>

            <textarea
              ref={inputRef}
              value={message}
              onChange={(event) =>
                setMessage(event.target.value)
              }
              onKeyDown={handleKeyDown}
              placeholder="Ask about syllabus, fees, placements, academics..."
              rows={1}
              disabled={loading}
            />

            <button
              className="send-button"
              onClick={() => sendMessage()}
              disabled={!message.trim() || loading}
              aria-label="Send message"
            >
              {loading ? "…" : "➤"}
            </button>
          </div>

          <p className="footer-note">
            College AI answers using information from your
            uploaded college documents.
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;