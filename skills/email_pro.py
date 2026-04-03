import imaplib
import email
from email.header import decode_header
import os

class EmailProSkill:
    def __init__(self):
        # Now these will automatically grab the data from your .env file
        self.email_user = os.getenv("CIPHER_EMAIL")
        self.email_pass = os.getenv("CIPHER_EMAIL_PASS")
        
        self.imap_server = "imap.gmail.com"
        
        # Security check
        if not self.email_user or not self.email_pass:
            print(">> [EmailPro Warning] Credentials missing in .env file!")
        else:
            print(">> Email Pro Skill: ONLINE (Secure Environment Active)")

    def _clean_header(self, header_val):
        """Decodes and cleans email headers for voice output."""
        if not header_val:
            return "No Subject"
        decoded = decode_header(header_val)
        subject, encoding = decoded[0]
        if isinstance(subject, bytes):
            return subject.decode(encoding or "utf-8", errors="ignore")
        return str(subject)

    def execute(self, command: str) -> str | None:
        try:
            if not command:
                return None

            cmd = command.lower().strip()

            # --- TRIGGER DETECTION ---
            triggers = ["unread emails", "check my mail", "any new emails", "check inbox"]
            if not any(t in cmd for t in triggers):
                return None

            if not self.email_user or not self.email_pass:
                return "Sir, my email credentials have not been configured in the system environment."

            print(f">> [EmailPro] Accessing the secure server to check your inbox...")
            
            # Connection logic
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_user, self.email_pass)
            mail.select("inbox")

            status, messages = mail.search(None, "UNSEEN")
            email_ids = messages[0].split()

            if not email_ids:
                mail.logout()
                return "Sir, your inbox is clear. You have no unread emails at this time."

            summaries = []
            # Limit to the 3 most recent to keep voice output concise
            for eid in email_ids[-3:]:
                _, msg_data = mail.fetch(eid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                
                subject = self._clean_header(msg["Subject"])
                sender = self._clean_header(msg["From"]).split('<')[0].strip()
                
                summaries.append(f"An email from {sender} regarding {subject}")

            mail.logout()
            
            response = f"Sir, you have {len(email_ids)} unread emails. The latest include: "
            return response + ". ".join(summaries)

        except Exception as e:
            print(f"[EmailPro Error] {e}")
            return "Sir, I encountered an authentication or connection error while accessing your mail server."