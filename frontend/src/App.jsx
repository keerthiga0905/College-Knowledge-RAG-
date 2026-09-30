import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const CIT_CATEGORIES = [
  {
    category: "Academics",
    icon: "📚",
    prompts: [
      { title: "Attendance Rules", msg: "What are the attendance requirements and condonation rules at CIT Coimbatore?" },
      { title: "Academic Regulations", msg: "Explain the CBCS grading system and CGPA calculation at CIT." },
      { title: "AIML & CSE Syllabus", msg: "What is the course curriculum for B.E. Computer Science and AIML?" },
      { title: "Exam Schedule", msg: "When are CAT 1, CAT 2, and end semester exams held at CIT?" },
    ],
  },
  {
    category: "Admissions & Fees",
    icon: "🎓",
    prompts: [
      { title: "Admission Eligibility", msg: "How to get admission in B.E. / B.Tech through TNEA counseling at CIT?" },
      { title: "Tuition Fee Structure", msg: "What is the annual fee structure for government-aided and self-supporting courses?" },
      { title: "Scholarships Available", msg: "What scholarships are provided for First Generation graduates and SC/ST students at CIT?" },
      { title: "Postgraduate Courses", msg: "What M.E. / M.Tech and MCA programs are offered at CIT Coimbatore?" },
    ],
  },
  {
    category: "Departments",
    icon: "🏛️",
    prompts: [
      { title: "Engineering Departments", msg: "List all academic engineering departments and programs at CIT." },
      { title: "Research & Industry MoUs", msg: "What companies have Centers of Excellence and MoUs with CIT Coimbatore?" },
      { title: "Faculty & Centers", msg: "Tell me about faculty qualifications and research facilities at CIT." },
    ],
  },
  {
    category: "Placements & Training",
    icon: "💼",
    prompts: [
      { title: "Placement Statistics", msg: "What is the highest and average salary package offered at CIT Coimbatore?" },
      { title: "Top Recruiters", msg: "Which top companies visit CIT for campus recruitment?" },
      { title: "Placement Training", msg: "What pre-placement training is provided by the Career Guidance and Placement Cell (CGPC)?" },
    ],
  },
  {
    category: "Campus Facilities",
    icon: "🏢",
    prompts: [
      { title: "Central Library", msg: "What are the working hours and facilities in the CIT Central Library?" },
      { title: "Hostel Facilities", msg: "Describe the men's and women's hostel amenities and mess facilities at CIT." },
      { title: "Student Clubs & Fests", msg: "What student clubs, NSS, NCC, and cultural fests like YUGAM exist at CIT?" },
    ],
  },
];

const DEFAULT_USER = {
  user_id: "cit_student_user",
  name: "CIT Student",
  email: "student@cit.edu.in",
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
  const [activeCategoryIndex, setActiveCategoryIndex] = useState(0);

  // Admin Modal state
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [stats, setStats] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadCategory, setUploadCategory] = useState("01_College_information");
  const [webUrl, setWebUrl] = useState("");
  const [adminStatusMsg, setAdminStatusMsg] = useState("");
  const [adminLoading, setAdminLoading] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  /* -------------------------------------------------------
     AUTO INITIALIZE USER & HEALTH CHECK
  ------------------------------------------------------- */

  useEffect(() => {
    async function initUser() {
      try {
        const healthRes = await fetch(`${API_BASE}/health`);
        if (healthRes.ok) {
          setBackendOnline(true);
        }
      } catch {
        setBackendOnline(false);
      }

      const savedUser = localStorage.getItem("cit_ai_user");
      if (savedUser) {
        try {
          setUser(JSON.parse(savedUser));
          return;
        } catch {
          localStorage.removeItem("cit_ai_user");
        }
      }

      try {
        const response = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            name: "CIT Student",
            email: "student@cit.edu.in",
          }),
        });

        if (response.ok) {
          const data = await response.json();
          setUser(data);
          localStorage.setItem("cit_ai_user", JSON.stringify(data));
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
        { headers: { Accept: "application/json" } }
      );
      if (!response.ok) return;
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
     OPEN CONVERSATION
  ------------------------------------------------------- */

  async function openConversation(id) {
    if (!id) return;

    try {
      setLoading(true);
      const response = await fetch(
        `${API_BASE}/conversations/${encodeURIComponent(id)}`,
        { headers: { Accept: "application/json" } }
      );

      if (!response.ok) throw new Error("Could not load conversation");
      const data = await response.json();
      setConversationId(id);

      const loadedMessages = data?.messages || data?.conversation?.messages || [];
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
        setMessages((previous) => [...previous, data.assistant_message]);
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
            "⚠️ Could not connect to the CIT Knowledge AI backend. Please ensure the backend server is running on port 8000.",
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

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  /* -------------------------------------------------------
     FETCH ADMIN DATASET STATS
  ------------------------------------------------------- */

  async function fetchStats() {
    try {
      const res = await fetch(`${API_BASE}/admin/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.error("Failed to fetch admin stats:", e);
    }
  }

  function openAdminModal() {
    setShowAdminModal(true);
    setAdminStatusMsg("");
    fetchStats();
  }

  /* -------------------------------------------------------
     UPLOAD DOCUMENT (ADMIN)
  ------------------------------------------------------- */

  async function handleDocumentUpload(e) {
    e.preventDefault();
    if (!uploadFile) return;

    setAdminLoading(true);
    setAdminStatusMsg("Uploading and processing document into CIT vector database...");

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("category", uploadCategory);

    try {
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (res.ok) {
        setAdminStatusMsg(`✅ Success: ${data.message || "Document processed and indexed into ChromaDB!"}`);
        setUploadFile(null);
        fetchStats();
      } else {
        setAdminStatusMsg(`❌ Error: ${data.detail || "Upload failed"}`);
      }
    } catch (err) {
      setAdminStatusMsg(`❌ Upload failed: ${err.message}`);
    } finally {
      setAdminLoading(false);
    }
  }

  /* -------------------------------------------------------
     INGEST WEB URL (ADMIN)
  ------------------------------------------------------- */

  async function handleUrlIngest(e) {
    e.preventDefault();
    if (!webUrl.trim()) return;

    setAdminLoading(true);
    setAdminStatusMsg("Scraping CIT webpage and generating embeddings...");

    try {
      const res = await fetch(`${API_BASE}/admin/ingest-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: webUrl, category: uploadCategory }),
      });

      const data = await res.json();
      if (res.ok) {
        setAdminStatusMsg(`✅ Success: ${data.message || "Web page ingested into CIT knowledge base!"}`);
        setWebUrl("");
        fetchStats();
      } else {
        setAdminStatusMsg(`❌ Error: ${data.detail || "URL ingestion failed"}`);
      }
    } catch (err) {
      setAdminStatusMsg(`❌ Error: ${err.message}`);
    } finally {
      setAdminLoading(false);
    }
  }

  /* -------------------------------------------------------
     REINDEX KNOWLEDGE BASE (ADMIN)
  ------------------------------------------------------- */

  async function handleReindex() {
    setAdminLoading(true);
    setAdminStatusMsg("Rebuilding CIT vector database embeddings...");

    try {
      const res = await fetch(`${API_BASE}/admin/reindex`, { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        setAdminStatusMsg(`✅ Complete: ${data.message || "Knowledge Base Reindexed Successfully!"}`);
        fetchStats();
      } else {
        setAdminStatusMsg(`❌ Reindex Error: ${data.detail || "Reindex failed"}`);
      }
    } catch (err) {
      setAdminStatusMsg(`❌ Error: ${err.message}`);
    } finally {
      setAdminLoading(false);
    }
  }

  /* -------------------------------------------------------
     FORMAT TIME & TITLES
  ------------------------------------------------------- */

  function formatTime(dateValue) {
    if (!dateValue) return "";
    const date = new Date(dateValue);
    if (Number.isNaN(date.getTime())) return "";
    return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  }

  function getConversationTitle(conversation) {
    return (
      conversation?.title ||
      conversation?.name ||
      conversation?.last_message ||
      "CIT Conversation"
    );
  }

  /* -------------------------------------------------------
     SOURCE CITATION COMPONENT
  ------------------------------------------------------- */

  function SourceCard({ source }) {
    const filename = source?.document_filename || source?.filename || "Official CIT Document";
    const category = source?.category || "CIT Knowledge Base";
    const page = source?.page_number !== undefined ? `Page ${source.page_number}` : "";
    const citWebUrl = "https://www.cit.edu.in";

    return (
      <a
        href={citWebUrl}
        target="_blank"
        rel="noreferrer"
        className="source-card"
        title="View CIT Official Information Source"
      >
        <div className="source-icon">📄</div>
        <div className="source-info">
          <div className="source-name">{filename}</div>
          <div className="source-meta">
            <span>{category}</span>
            {page && <span> • {page}</span>}
          </div>
        </div>
        <span className="source-external">↗</span>
      </a>
    );
  }

  function Sources({ sources }) {
    if (!Array.isArray(sources) || sources.length === 0) return null;

    const uniqueSources = sources.filter((source, index, array) => {
      const key = `${source?.document_filename}-${source?.page_number}`;
      return index === array.findIndex((item) => `${item?.document_filename}-${item?.page_number}` === key);
    });

    return (
      <div className="sources-section">
        <div className="sources-heading">
          <span className="source-badge-icon">📍</span>
          <span>Official CIT Sources & References ({uniqueSources.length})</span>
        </div>
        <div className="sources-list">
          {uniqueSources.map((source, index) => (
            <SourceCard key={`${source?.document_filename}-${index}`} source={source} />
          ))}
        </div>
      </div>
    );
  }

  /* -------------------------------------------------------
     MARKDOWN ANSWER COMPONENT
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
                <a {...props} target="_blank" rel="noreferrer">
                  {children}
                </a>
              );
            },
            code({ inline, children, ...props }) {
              if (inline) return <code {...props}>{children}</code>;
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
     WELCOME SCREEN WITH CATEGORY SELECTION
  ------------------------------------------------------- */

  function WelcomeScreen() {
    const activeCategory = CIT_CATEGORIES[activeCategoryIndex];

    return (
      <div className="welcome-screen">
        <div className="cit-badge-hero">
          <div className="cit-hero-logo">🏛️</div>
          <div className="cit-hero-tag">Coimbatore Institute of Technology</div>
        </div>

        <h1>CIT Knowledge AI Assistant</h1>

        <p className="welcome-subtitle">
          Ask questions about academics, syllabus, regulations, fees, departments, placements, and campus facilities. Grounded in official CIT documents.
        </p>

        {/* CATEGORY TABS */}
        <div className="category-tabs">
          {CIT_CATEGORIES.map((cat, idx) => (
            <button
              key={cat.category}
              className={`category-tab ${activeCategoryIndex === idx ? "active" : ""}`}
              onClick={() => setActiveCategoryIndex(idx)}
            >
              <span>{cat.icon}</span>
              <span>{cat.category}</span>
            </button>
          ))}
        </div>

        {/* PROMPTS GRID FOR ACTIVE CATEGORY */}
        <div className="quick-grid">
          {activeCategory.prompts.map((item) => (
            <button
              className="quick-card"
              key={item.title}
              onClick={() => sendMessage(item.msg)}
            >
              <div className="quick-text">
                <strong>{item.title}</strong>
                <span>"{item.msg}"</span>
              </div>
              <span className="quick-arrow">➔</span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  /* -------------------------------------------------------
     MAIN RENDER
  ------------------------------------------------------- */

  return (
    <div className="app-shell">
      {/* MOBILE OVERLAY */}
      {mobileSidebar && <div className="mobile-overlay" onClick={() => setMobileSidebar(false)} />}

      {/* SIDEBAR */}
      <aside className={`sidebar ${mobileSidebar ? "sidebar-open" : ""}`}>
        <div className="sidebar-top">
          <div className="brand">
            <div className="brand-logo">🏛️</div>
            <div>
              <h2>CIT Knowledge AI</h2>
              <span className="cit-motto">Progress Through Technology</span>
            </div>
          </div>

          <button className="new-chat-button" onClick={startNewConversation}>
            <span>＋</span> New Conversation
          </button>

          <button className="admin-button" onClick={openAdminModal}>
            <span>⚙️</span> Dataset & Ingestion
          </button>

          <div className="recent-heading">Recent Conversations</div>

          <div className="conversation-list">
            {conversations.length === 0 ? (
              <div className="empty-conversations">
                <div>💬</div>
                <span>No previous conversations</span>
              </div>
            ) : (
              conversations.map((conversation, index) => {
                const id = conversation.conversation_id || conversation.id;
                return (
                  <button
                    key={id || index}
                    className={`conversation-item ${conversationId === id ? "active" : ""}`}
                    onClick={() => openConversation(id)}
                  >
                    <span className="conversation-icon">💬</span>
                    <span className="conversation-title">{getConversationTitle(conversation)}</span>
                  </button>
                );
              })
            )}
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="profile">
            <div className="avatar">{(user?.name || "C").charAt(0).toUpperCase()}</div>
            <div className="profile-info">
              <strong>{user?.name || "CIT Student"}</strong>
              <span>{user?.email || "student@cit.edu.in"}</span>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN AREA */}
      <main className="main-area">
        {/* TOPBAR HEADER */}
        <header className="topbar">
          <div className="header-left">
            <button className="mobile-menu" onClick={() => setMobileSidebar(true)} aria-label="Open menu">
              ☰
            </button>
            <div>
              <h1>CIT Knowledge AI</h1>
              <p>Coimbatore Institute of Technology — Official RAG Knowledge System</p>
            </div>
          </div>

          <div className="topbar-right">
            <button className="admin-pill-btn" onClick={openAdminModal}>
              📊 Dataset Manager
            </button>
            <div className={`status ${backendOnline ? "online" : "offline"}`}>
              <span className="status-dot" />
              {backendOnline ? "CIT AI Online" : "Backend Offline"}
            </div>
          </div>
        </header>

        {/* CHAT MESSAGES AREA */}
        <section className="chat-area">
          {messages.length === 0 ? (
            <WelcomeScreen />
          ) : (
            <div className="messages-container">
              {messages.map((item, index) => {
                const isUser = item.role === "user";
                return (
                  <div
                    key={item.message_id || `${item.role}-${index}`}
                    className={`message-row ${isUser ? "user-row" : "assistant-row"}`}
                  >
                    {!isUser && <div className="assistant-avatar">🏛️</div>}

                    <div
                      className={`message-content ${isUser ? "user-message" : "assistant-message"} ${
                        item.error ? "error-message" : ""
                      }`}
                    >
                      {isUser ? <p>{item.content}</p> : <MarkdownAnswer content={item.content} />}

                      {!isUser && <Sources sources={item.sources} />}

                      <span className="message-time">{formatTime(item.created_at)}</span>
                    </div>

                    {isUser && <div className="user-avatar">{(user.name || "S").charAt(0).toUpperCase()}</div>}
                  </div>
                );
              })}

              {loading && (
                <div className="message-row assistant-row">
                  <div className="assistant-avatar">🏛️</div>
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

        {/* INPUT COMPOSER */}
        <footer className="composer-area">
          <div className="composer">
            <div className="composer-icon">✦</div>

            <textarea
              ref={inputRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about CIT academics, regulations, syllabus, fees, placements..."
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
            Grounded in official CIT Coimbatore documents & vector search pipeline.
          </p>
        </footer>
      </main>

      {/* DATASET / ADMIN MANAGEMENT MODAL */}
      {showAdminModal && (
        <div className="modal-overlay" onClick={() => setShowAdminModal(false)}>
          <div className="modal-container" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">
                <span>⚙️</span> CIT Knowledge Base & Ingestion Manager
              </div>
              <button className="modal-close" onClick={() => setShowAdminModal(false)}>
                ✕
              </button>
            </div>

            <div className="modal-body">
              {/* STATS OVERVIEW */}
              <div className="admin-stats-grid">
                <div className="stat-card">
                  <div className="stat-value">{stats?.total_chunks ?? 43}</div>
                  <div className="stat-label">Vector Chunks in ChromaDB</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{stats?.total_documents ?? 13}</div>
                  <div className="stat-label">Indexed Documents</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">5</div>
                  <div className="stat-label">CIT Categories</div>
                </div>
              </div>

              {adminStatusMsg && <div className="admin-status-box">{adminStatusMsg}</div>}

              {/* UPLOAD FILE FORM */}
              <div className="admin-section">
                <h3>📄 Add Official CIT Document (PDF / TXT / DOCX)</h3>
                <form onSubmit={handleDocumentUpload} className="admin-form">
                  <div className="form-group">
                    <label>Select Category:</label>
                    <select value={uploadCategory} onChange={(e) => setUploadCategory(e.target.value)}>
                      <option value="01_College_information">01_College_information (Overview, Depts)</option>
                      <option value="02_Syllabus">02_Syllabus (Curriculum, Regulations)</option>
                      <option value="03_Academic_Calendar">03_Academic_Calendar (Events, Schedules)</option>
                      <option value="04_Lab_Manuals">04_Lab_Manuals (Lab Facilities, Rules)</option>
                      <option value="05_Fees_Placement_Funding">05_Fees_Placement_Funding (Fees, Placements)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Choose File:</label>
                    <input
                      type="file"
                      accept=".pdf,.txt,.docx,.doc,.html"
                      onChange={(e) => setUploadFile(e.target.files[0])}
                    />
                  </div>

                  <button type="submit" className="admin-submit-btn" disabled={!uploadFile || adminLoading}>
                    {adminLoading ? "Processing..." : "Upload & Index Document"}
                  </button>
                </form>
              </div>

              {/* INGEST URL FORM */}
              <div className="admin-section">
                <h3>🌐 Add CIT Website URL</h3>
                <form onSubmit={handleUrlIngest} className="admin-form">
                  <div className="form-group">
                    <label>CIT Website URL:</label>
                    <input
                      type="url"
                      placeholder="https://www.cit.edu.in/academics/curriculum"
                      value={webUrl}
                      onChange={(e) => setWebUrl(e.target.value)}
                    />
                  </div>
                  <button type="submit" className="admin-submit-btn" disabled={!webUrl.trim() || adminLoading}>
                    {adminLoading ? "Scraping & Indexing..." : "Ingest Web Page"}
                  </button>
                </form>
              </div>

              {/* REINDEX ALL */}
              <div className="admin-section">
                <h3>🔄 Knowledge Base Re-indexing</h3>
                <p className="admin-desc">Rebuild all vector embeddings from the CIT data directory into ChromaDB.</p>
                <button className="admin-reindex-btn" onClick={handleReindex} disabled={adminLoading}>
                  Rebuild Vector Index Now
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;