import json
import tempfile
import unittest
from pathlib import Path

from repository_analyzer import analyze_repository
from deploybuddy import _resolve_service_type
from rag_1 import ArchitectureRAG


class RepositoryAnalyzerTests(unittest.TestCase):
    def _make_sample_repo(self, root: Path):
        (root / "package.json").write_text(
            json.dumps(
                {
                    "scripts": {"dev": "next dev", "start": "next start"},
                    "dependencies": {
                        "next": "15.0.0",
                        "react": "19.0.0",
                        "@prisma/client": "6.0.0",
                    },
                }
            ),
            encoding="utf-8",
        )
        (root / "requirements.txt").write_text(
            "fastapi==0.115.0\nuvicorn[standard]\npsycopg2-binary\n",
            encoding="utf-8",
        )
        (root / "docker-compose.yml").write_text(
            "services:\n  db:\n    image: postgres:16\n  redis:\n    image: redis:7\n",
            encoding="utf-8",
        )
        (root / ".env.example").write_text(
            "DATABASE_URL=\nAPI_KEY=change-me\n# COMMENTED_OUT=value\n",
            encoding="utf-8",
        )
        (root / ".env").write_text("SECRET_KEY=do-not-read\n", encoding="utf-8")
        (root / "node_modules").mkdir()
        (root / "node_modules" / "ignored.js").write_text("ignored", encoding="utf-8")
        (root / "app").mkdir()
        (root / "app" / "api").mkdir()
        (root / "app" / "api" / "route.ts").write_text(
            "import { NextRequest } from 'next/server';\n"
            "export function GET() { return Response.json({ ok: true }); }\n",
            encoding="utf-8",
        )

    def test_detects_stack_and_filters_sensitive_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_sample_repo(root)

            profile = analyze_repository(repo_path=str(root))
            context = profile.to_context()

            self.assertIn("Next.js", profile.detected_stack)
            self.assertIn("FastAPI", profile.detected_stack)
            self.assertIn("PostgreSQL", profile.databases)
            self.assertIn("backend", profile.service_types)
            self.assertIn("frontend", profile.service_types)
            self.assertIn("DATABASE_URL", profile.env_vars_detected)
            self.assertIn("API_KEY", profile.env_vars_detected)
            self.assertIn("Skipped sensitive files", "\n".join(profile.warnings))
            self.assertNotIn("SECRET_KEY", context)
            self.assertNotIn("node_modules/ignored.js", context)

    def test_service_type_alias_keeps_fullstack_from_becoming_ml(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "requirements.txt").write_text(
                "fastapi==0.115.0\nchromadb\nsentence-transformers\n",
                encoding="utf-8",
            )

            profile = analyze_repository(repo_path=str(root))
            service_type = _resolve_service_type(profile, "Fullstack App")

            self.assertEqual(service_type, "web_application")
            self.assertEqual(
                ArchitectureRAG(None, None, None)._infer_primary_workload(
                    {"framework": "FastAPI, RAG/Vector Search", "type": ",".join(profile.service_types)},
                    {"service_type": service_type},
                ),
                "web_application",
            )


if __name__ == "__main__":
    unittest.main()
