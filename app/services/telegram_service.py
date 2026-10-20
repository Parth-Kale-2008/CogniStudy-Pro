"""
Production Telegram Bot Service.
Processes webhook updates, document uploads, interactive commands, and RAG queries.
"""

from typing import Dict, Any, Optional
import httpx

from app.config import settings
from app.core.logging import logger
from app.models.schemas import StudyMode, QueryRequest
from app.rag.engine import CogniStudyRAGEngine
from app.services.chat_service import chat_service


class TelegramService:
    """
    Handles 24/7 Telegram updates, file downloads, commands, and messaging.
    """

    def __init__(self, rag_engine: Optional[CogniStudyRAGEngine] = None):
        self.rag_engine = rag_engine or CogniStudyRAGEngine()
        self.token = (settings.TELEGRAM_BOT_TOKEN or "").strip().replace("\n", "").replace("\r", "")

    async def send_message(self, chat_id: int | str, text: str) -> bool:
        """
        Sends message to a Telegram chat, automatically splitting messages > 4000 chars.
        """
        if not self.token:
            logger.warning("Telegram token is not configured. Skipping send_message.")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        # Split message if it exceeds Telegram's 4096 limit
        chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)] or [""]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for chunk in chunks:
                try:
                    payload = {
                        "chat_id": chat_id,
                        "text": chunk,
                        "disable_web_page_preview": True
                    }
                    resp = await client.post(url, json=payload)
                    if resp.status_code != 200:
                        logger.error(f"Telegram API error {resp.status_code}: {resp.text}")
                except Exception as e:
                    logger.error(f"Exception sending message to Telegram chat {chat_id}: {e}")
                    return False
        return True

    async def handle_update(self, update: Dict[str, Any]) -> Dict[str, bool]:
        """
        Main entry point for incoming Telegram Webhook payloads.
        """
        message = update.get("message") or update.get("edited_message")
        if not message:
            return {"ok": True}

        chat_id = message.get("chat", {}).get("id")
        if not chat_id:
            return {"ok": True}

        user_id = f"tg_{chat_id}"
        text = (message.get("text") or message.get("caption") or "").strip()
        document = message.get("document")

        # 1. Handle Commands
        if text.startswith("/"):
            await self._handle_command(chat_id, user_id, text)
            return {"ok": True}

        # 2. Handle Document Uploads (PDF, DOCX, TXT)
        if document:
            await self._handle_document(chat_id, user_id, document)
            return {"ok": True}

        # 3. Handle Regular Questions / Queries
        if text:
            await self._handle_query(chat_id, user_id, text)
            return {"ok": True}

        return {"ok": True}

    async def _handle_command(self, chat_id: int | str, user_id: str, text: str) -> None:
        cmd_parts = text.split()
        command = cmd_parts[0].lower().split("@")[0]

        if command == "/start":
            welcome_msg = (
                "🚀 *Welcome to CogniStudy Pro™ — 24/7 RAG Document Assistant!*\n\n"
                "I am your intelligent enterprise study and research copilot.\n\n"
                "💡 *Quick Start:*\n"
                "1️⃣ Send me any PDF, DOCX, or TXT file.\n"
                "2️⃣ I will index and extract semantic context.\n"
                "3️⃣ Ask me any questions, request summaries, or take quizzes!\n\n"
                "⚡ *Commands:*\n"
                "• `/mode <student|executive|researcher|exam_cram>` - Switch study mode\n"
                "• `/modes` - See descriptions of all 4 study modes\n"
                "• `/quiz [topic]` - Generate an instant active recall quiz\n"
                "• `/stats` - View your indexed documents and chunks\n"
                "• `/clear` - Purge your indexed study notes\n"
                "• `/help` - Show instructions\n"
            )
            await self.send_message(chat_id, welcome_msg)

        elif command == "/help":
            help_msg = (
                "📖 *CogniStudy Pro Help Center*\n\n"
                "• *Upload Notes:* Attach any PDF, DOCX, or TXT file directly into this chat.\n"
                "• *Ask Questions:* Simply type your question after uploading.\n"
                "• *Change Mode:* Type `/mode executive` or `/mode student`.\n"
                "• *Generate Quiz:* Type `/quiz` or `/quiz neural networks`."
            )
            await self.send_message(chat_id, help_msg)

        elif command == "/modes":
            modes_msg = (
                "🎓 *CogniStudy Pro Study Modes:*\n\n"
                "1. `student` (Default): Socratic explanation, step-by-step logic, real-life analogies, and clear definitions.\n"
                "2. `executive`: High-level executive summary, bullet points, key takeaways, and strategic action items.\n"
                "3. `researcher`: Academic rigor, primary source citations, and exact quotes.\n"
                "4. `exam_cram`: High-yield test topics, active recall, and mnemonics."
            )
            await self.send_message(chat_id, modes_msg)

        elif command == "/mode":
            if len(cmd_parts) > 1:
                requested_mode = cmd_parts[1].lower()
                try:
                    mode_enum = StudyMode(requested_mode)
                    chat_service.set_mode(user_id, mode_enum)
                    await self.send_message(chat_id, f"✅ Study mode switched to *{mode_enum.value.upper()}*!")
                except ValueError:
                    await self.send_message(
                        chat_id,
                        "⚠️ Invalid mode. Choose from: `student`, `executive`, `researcher`, `exam_cram`."
                    )
            else:
                curr_mode = chat_service.get_mode(user_id)
                await self.send_message(chat_id, f"Current active mode: *{curr_mode.value.upper()}*.\nUse `/mode <name>` to change.")

        elif command == "/quiz":
            topic = " ".join(cmd_parts[1:]) if len(cmd_parts) > 1 else None
            await self.send_message(chat_id, "⏳ Generating active recall quiz from your notes...")
            quiz_resp = self.rag_engine.generate_quiz(user_id=user_id, topic=topic, num_questions=3)
            
            quiz_lines = [f"📝 *Quiz: {quiz_resp.topic}*\n"]
            for q in quiz_resp.questions:
                quiz_lines.append(f"*{q.id}. {q.question}*")
                for opt in q.options:
                    quiz_lines.append(f"  {opt}")
                correct_letter = ["A", "B", "C", "D"][q.correct_index]
                quiz_lines.append(f"👉 *Answer:* Option {correct_letter}")
                quiz_lines.append(f"💡 *Explanation:* {q.explanation}\n")

            await self.send_message(chat_id, "\n".join(quiz_lines))

        elif command == "/stats":
            docs = self.rag_engine.get_user_documents(user_id)
            total_chunks = sum(d.get("chunk_count", 0) for d in docs)
            curr_mode = chat_service.get_mode(user_id)
            stats_msg = (
                f"📊 *Your Knowledge Base Stats:*\n\n"
                f"• Active Mode: `{curr_mode.value.upper()}`\n"
                f"• Documents Indexed: `{len(docs)}`\n"
                f"• Total Semantic Chunks: `{total_chunks}`\n"
            )
            await self.send_message(chat_id, stats_msg)

        elif command == "/clear":
            self.rag_engine.clear_user_index(user_id)
            chat_service.clear_history(user_id)
            await self.send_message(chat_id, "🗑️ All uploaded notes and conversation memory have been cleared.")

        else:
            await self.send_message(chat_id, "Unknown command. Type `/help` for available options.")

    async def _handle_document(self, chat_id: int | str, user_id: str, document: Dict[str, Any]) -> None:
        file_id = document.get("file_id")
        file_name = document.get("file_name", "document.pdf")

        if not self.token:
            await self.send_message(chat_id, "⚠️ Bot token is not configured on the server.")
            return

        await self.send_message(chat_id, f"⏳ Downloading and indexing *{file_name}*...")

        try:
            file_info_url = f"https://api.telegram.org/bot{self.token}/getFile?file_id={file_id}"
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(file_info_url)
                file_path = resp.json().get("result", {}).get("file_path")
                if not file_path:
                    await self.send_message(chat_id, "❌ Failed to fetch file path from Telegram.")
                    return

                download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
                file_resp = await client.get(download_url)
                content = file_resp.content

            result = self.rag_engine.ingest_document(
                user_id=user_id,
                content=content,
                filename=file_name
            )

            if result.chunks_indexed > 0:
                await self.send_message(
                    chat_id,
                    f"✅ *Document Ready!*\n"
                    f"Successfully indexed *{result.chunks_indexed}* semantic chunks.\n\n"
                    f"You can now ask questions about *{file_name}*!"
                )
            else:
                await self.send_message(chat_id, "⚠️ Could not extract readable text from this file.")

        except Exception as e:
            logger.error(f"Error indexing telegram document: {e}", exc_info=True)
            await self.send_message(chat_id, f"❌ Failed to process document: {str(e)}")

    async def _handle_query(self, chat_id: int | str, user_id: str, text: str) -> None:
        active_mode = chat_service.get_mode(user_id)
        query_req = QueryRequest(
            user_id=user_id,
            question=text,
            mode=active_mode,
            top_k=4
        )

        resp = self.rag_engine.query(query_req)

        answer_body = resp.answer

        if resp.citations:
            citation_lines = ["\n\n📌 *Sources & Citations:*"]
            for c in resp.citations[:3]:
                page_str = f" (Page {c.page_number})" if c.page_number else ""
                citation_lines.append(f"• `{c.source_file}`{page_str}")
            answer_body += "\n".join(citation_lines)

        await self.send_message(chat_id, answer_body)
