/**
 * CogniStudy Pro™ — Interactive Web Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
    // State
    let activeMode = "student";
    let userId = localStorage.getItem("cogni_user_id") || "default";
    let isProcessing = false;
    let documentsList = [];

    // Elements
    const systemStatus = document.getElementById("systemStatus");
    const statusText = document.getElementById("statusText");
    const modeCards = document.querySelectorAll(".mode-card");
    const activeModeChip = document.getElementById("activeModeChip");
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const uploadProgress = document.getElementById("uploadProgress");
    const docList = document.getElementById("docList");
    const docCountBadge = document.getElementById("docCountBadge");
    const btnClearIndex = document.getElementById("btnClearIndex");
    const chatMessages = document.getElementById("chatMessages");
    const welcomeHero = document.getElementById("welcomeHero");
    const chatInput = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendBtn");
    const toastMsg = document.getElementById("toastMsg");

    // Modals
    const citationModal = document.getElementById("citationModal");
    const closeCitationModal = document.getElementById("closeCitationModal");
    const citationSourceText = document.getElementById("citationSourceText");
    const citationSnippetText = document.getElementById("citationSnippetText");

    const quizModal = document.getElementById("quizModal");
    const closeQuizModal = document.getElementById("closeQuizModal");
    const btnOpenQuizModal = document.getElementById("btnOpenQuizModal");
    const quizModalBody = document.getElementById("quizModalBody");

    const telegramModal = document.getElementById("telegramModal");
    const btnTelegramModal = document.getElementById("btnTelegramModal");
    const closeTelegramModal = document.getElementById("closeTelegramModal");
    const telegramStatusContent = document.getElementById("telegramStatusContent");

    const modeLabels = {
        student: "🎓 Student",
        executive: "💼 Executive",
        researcher: "🔬 Researcher",
        exam_cram: "⚡ Exam Cram"
    };

    // --- Toast Helper ---
    function showToast(text, duration = 3000) {
        toastMsg.textContent = text;
        toastMsg.style.display = "block";
        setTimeout(() => {
            toastMsg.style.display = "none";
        }, duration);
    }

    // --- Health Check ---
    async function checkHealth() {
        try {
            const resp = await fetch("/health");
            if (resp.ok) {
                const data = await resp.json();
                statusText.textContent = `Online • ${data.app_name} v${data.version}`;
                systemStatus.style.borderColor = "rgba(16, 185, 129, 0.4)";
            } else {
                statusText.textContent = "Offline / Error";
            }
        } catch (e) {
            statusText.textContent = "Server Unavailable";
        }
    }

    // --- Mode Selection ---
    modeCards.forEach(card => {
        card.addEventListener("click", () => {
            modeCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            activeMode = card.getAttribute("data-mode");
            activeModeChip.textContent = modeLabels[activeMode] || activeMode;
            showToast(`Switched persona to: ${modeLabels[activeMode]}`);
        });
    });

    // --- Suggestion Chips ---
    document.querySelectorAll(".suggestion-chip").forEach(btn => {
        btn.addEventListener("click", () => {
            const prompt = btn.getAttribute("data-prompt");
            chatInput.value = prompt;
            sendMessage();
        });
    });

    // --- Ingestion & Upload ---
    dropzone.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("drag-over");
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("drag-over");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("drag-over");
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    async function handleFileUpload(file) {
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);
        formData.append("user_id", userId);

        uploadProgress.style.display = "block";
        showToast(`Indexing ${file.name}...`);

        try {
            const resp = await fetch("/api/v1/upload", {
                method: "POST",
                body: formData
            });

            const data = await resp.json();

            if (resp.ok && data.chunks_indexed > 0) {
                showToast(`✅ Successfully indexed ${data.chunks_indexed} chunks from ${file.name}`);
                fetchDocuments();
            } else {
                showToast(`⚠️ ${data.message || "Could not extract chunks."}`);
            }
        } catch (err) {
            showToast(`❌ Upload error: ${err.message}`);
        } finally {
            uploadProgress.style.display = "none";
            fileInput.value = "";
        }
    }

    // --- Document Library ---
    async function fetchDocuments() {
        try {
            const resp = await fetch(`/api/v1/documents?user_id=${encodeURIComponent(userId)}`);
            if (resp.ok) {
                const data = await resp.json();
                documentsList = data.documents || [];
                renderDocuments();
            }
        } catch (e) {
            console.error("Failed to load documents", e);
        }
    }

    function renderDocuments() {
        docCountBadge.textContent = `${documentsList.length} docs`;
        if (documentsList.length === 0) {
            docList.innerHTML = `<div class="empty-docs">No documents indexed yet.</div>`;
            return;
        }

        docList.innerHTML = documentsList.map(doc => `
            <div class="doc-item">
                <span class="doc-name" title="${doc.filename}">${doc.filename}</span>
                <span class="doc-chunks">${doc.chunk_count} chunks</span>
            </div>
        `).join("");
    }

    btnClearIndex.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to clear your indexed knowledge base?")) return;
        try {
            const resp = await fetch(`/api/v1/documents?user_id=${encodeURIComponent(userId)}`, {
                method: "DELETE"
            });
            if (resp.ok) {
                showToast("🗑️ Knowledge base cleared.");
                fetchDocuments();
            }
        } catch (e) {
            showToast("Failed to clear index.");
        }
    });

    // --- Chat & RAG Query ---
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener("click", sendMessage);

    async function sendMessage() {
        const queryText = chatInput.value.trim();
        if (!queryText || isProcessing) return;

        isProcessing = true;
        sendBtn.disabled = true;
        chatInput.value = "";

        if (welcomeHero) welcomeHero.style.display = "none";

        // Append User Message
        appendUserMessage(queryText);

        // Append Thinking placeholder
        const thinkingId = "thinking-" + Date.now();
        appendThinkingMessage(thinkingId);

        try {
            const resp = await fetch("/api/v1/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: userId,
                    question: queryText,
                    mode: activeMode,
                    top_k: 4
                })
            });

            const data = await resp.json();

            removeElement(thinkingId);

            if (resp.ok) {
                appendAIMessage(data);
            } else {
                appendErrorMessage(data.detail || "Error querying knowledge base.");
            }
        } catch (err) {
            removeElement(thinkingId);
            appendErrorMessage(`Network error: ${err.message}`);
        } finally {
            isProcessing = false;
            sendBtn.disabled = false;
            chatInput.focus();
        }
    }

    function appendUserMessage(text) {
        const row = document.createElement("div");
        row.className = "message-row user-row";
        row.innerHTML = `
            <div class="message-content">
                <div class="user-bubble">${escapeHtml(text)}</div>
            </div>
            <div class="avatar avatar-user">
                <i class="bi bi-person-fill"></i>
            </div>
        `;
        chatMessages.appendChild(row);
        scrollToBottom();
    }

    function appendThinkingMessage(id) {
        const row = document.createElement("div");
        row.className = "message-row";
        row.id = id;
        row.innerHTML = `
            <div class="avatar avatar-ai">
                <i class="bi bi-cpu-fill"></i>
            </div>
            <div class="message-content">
                <div class="ai-bubble" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted);">
                    <span class="status-dot"></span>
                    <span>Retrieving context & synthesizing with ${modeLabels[activeMode]}...</span>
                </div>
            </div>
        `;
        chatMessages.appendChild(row);
        scrollToBottom();
    }

    function appendAIMessage(data) {
        const row = document.createElement("div");
        row.className = "message-row";

        const parsedAnswer = typeof marked !== "undefined" ? marked.parse(data.answer) : escapeHtml(data.answer);

        let citationsHtml = "";
        if (data.citations && data.citations.length > 0) {
            const pills = data.citations.map((c, i) => {
                const pageLabel = c.page_number ? `p. ${c.page_number}` : `chunk ${c.chunk_id || i+1}`;
                return `<button class="citation-pill" data-src="${escapeHtml(c.source_file)}" data-snippet="${escapeHtml(c.snippet)}">
                    <i class="bi bi-link-45deg"></i> ${escapeHtml(c.source_file)} (${pageLabel})
                </button>`;
            }).join("");

            citationsHtml = `
                <div class="citations-wrapper">
                    <span class="citations-label">Sources:</span>
                    ${pills}
                </div>
            `;
        }

        row.innerHTML = `
            <div class="avatar avatar-ai">
                <i class="bi bi-cpu-fill"></i>
            </div>
            <div class="message-content">
                <div class="ai-bubble">
                    ${parsedAnswer}
                    ${citationsHtml}
                    <div class="meta-footer">
                        <span>${modeLabels[data.mode] || data.mode} • ${data.chunks_retrieved} context chunks</span>
                        <span>⚡ ${data.response_time_ms} ms</span>
                    </div>
                </div>
            </div>
        `;

        chatMessages.appendChild(row);

        // Attach citation pill click listeners
        row.querySelectorAll(".citation-pill").forEach(pill => {
            pill.addEventListener("click", () => {
                const src = pill.getAttribute("data-src");
                const snippet = pill.getAttribute("data-snippet");
                openCitationModal(src, snippet);
            });
        });

        scrollToBottom();
    }

    function appendErrorMessage(msg) {
        const row = document.createElement("div");
        row.className = "message-row";
        row.innerHTML = `
            <div class="avatar avatar-ai" style="background: var(--accent-rose);">
                <i class="bi bi-exclamation-triangle-fill"></i>
            </div>
            <div class="message-content">
                <div class="ai-bubble" style="border-color: rgba(244, 63, 94, 0.4); color: #fca5a5;">
                    ${escapeHtml(msg)}
                </div>
            </div>
        `;
        chatMessages.appendChild(row);
        scrollToBottom();
    }

    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // --- Citation Modal ---
    function openCitationModal(source, snippet) {
        citationSourceText.textContent = `Source Document: ${source}`;
        citationSnippetText.textContent = snippet;
        citationModal.classList.add("open");
    }

    closeCitationModal.addEventListener("click", () => {
        citationModal.classList.remove("open");
    });

    // --- Quiz Modal ---
    btnOpenQuizModal.addEventListener("click", async () => {
        quizModal.classList.add("open");
        quizModalBody.innerHTML = `
            <div style="text-align: center; padding: 40px 0;">
                <div class="status-dot" style="margin: 0 auto 12px; width: 12px; height: 12px;"></div>
                <p style="color: var(--text-secondary);">Generating active recall questions from your notes...</p>
            </div>
        `;

        try {
            const resp = await fetch("/api/v1/quiz", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: userId, num_questions: 4 })
            });

            if (resp.ok) {
                const data = await resp.json();
                renderQuizQuestions(data);
            } else {
                quizModalBody.innerHTML = `<p style="color: var(--accent-rose); text-align: center;">Failed to generate quiz. Please upload notes first.</p>`;
            }
        } catch (e) {
            quizModalBody.innerHTML = `<p style="color: var(--accent-rose); text-align: center;">Network error while generating quiz.</p>`;
        }
    });

    function renderQuizQuestions(data) {
        if (!data.questions || data.questions.length === 0) {
            quizModalBody.innerHTML = `<p style="text-align: center; color: var(--text-muted);">No questions could be formulated. Try uploading more notes.</p>`;
            return;
        }

        const cards = data.questions.map((q, qIndex) => {
            const opts = q.options.map((opt, optIndex) => `
                <button class="quiz-option-btn" data-qid="${qIndex}" data-optindex="${optIndex}" data-correct="${q.correct_index}">
                    ${escapeHtml(opt)}
                </button>
            `).join("");

            return `
                <div class="quiz-card" id="quizCard-${qIndex}">
                    <div class="quiz-q-title">${q.id}. ${escapeHtml(q.question)}</div>
                    <div class="quiz-options">${opts}</div>
                    <div class="quiz-explanation" id="quizExp-${qIndex}">
                        💡 <strong>Explanation:</strong> ${escapeHtml(q.explanation)}
                    </div>
                </div>
            `;
        }).join("");

        quizModalBody.innerHTML = cards;

        // Attach option click logic
        quizModalBody.querySelectorAll(".quiz-option-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const qid = btn.getAttribute("data-qid");
                const chosenIdx = parseInt(btn.getAttribute("data-optindex"));
                const correctIdx = parseInt(btn.getAttribute("data-correct"));

                const parentCard = document.getElementById(`quizCard-${qid}`);
                const expBox = document.getElementById(`quizExp-${qid}`);

                parentCard.querySelectorAll(".quiz-option-btn").forEach((b, idx) => {
                    b.disabled = true;
                    if (idx === correctIdx) {
                        b.classList.add("correct");
                    } else if (idx === chosenIdx) {
                        b.classList.add("incorrect");
                    }
                });

                expBox.classList.add("show");
            });
        });
    }

    closeQuizModal.addEventListener("click", () => {
        quizModal.classList.remove("open");
    });

    // --- Telegram Info Modal ---
    btnTelegramModal.addEventListener("click", async () => {
        telegramModal.classList.add("open");
        telegramStatusContent.textContent = "Checking status...";
        try {
            const resp = await fetch("/telegram-info");
            const data = await resp.json();
            telegramStatusContent.innerHTML = `
                • Configured: ${data.telegram_configured ? '<span style="color:#10b981;">YES (Active)</span>' : '<span style="color:#f43f5e;">NO (Token Missing)</span>'}<br>
                • Token: ${data.token_preview}<br>
                • Webhook: ${data.webhook_url}
            `;
        } catch (e) {
            telegramStatusContent.textContent = "Could not fetch Telegram info.";
        }
    });

    closeTelegramModal.addEventListener("click", () => {
        telegramModal.classList.remove("open");
    });

    // Close modals on clicking overlay background
    [citationModal, quizModal, telegramModal].forEach(modal => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) modal.classList.remove("open");
        });
    });

    // Initial Load
    checkHealth();
    fetchDocuments();
});
