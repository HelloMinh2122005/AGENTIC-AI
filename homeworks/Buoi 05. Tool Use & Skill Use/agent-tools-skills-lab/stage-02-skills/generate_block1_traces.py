"""Tạo trace thật cho Block 1 theo đúng chuẩn Observer & TraceWriter của lab."""

import sys
import uuid
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from langchain_core.messages import AIMessage, HumanMessage
import paths
from agent import build_agent, capabilities
from observer import Observer
from trace import TraceWriter
from tests.conftest import ScriptedChatModel


def run_simulated_turn(prompt: str, scripted_responses: list[AIMessage], conv_id: str, turn_idx: int):
    model = ScriptedChatModel(responses=scripted_responses)
    agent = build_agent(model)
    observer = Observer(conversation_id=conv_id)
    run_id = uuid.uuid4().hex
    observer.start_turn(run_id)
    writer = TraceWriter(paths.TRACES_DIR, "stage-02-skills", conv_id, run_id, turn_idx)

    caps = capabilities()
    ev_user = observer.record("user_submitted", {"text": prompt, "tools": caps["tools"], "skills": caps["skills"]})
    writer.write(ev_user)

    messages = [HumanMessage(content=prompt)]
    observer.sync_messages(messages)

    for mode, chunk in agent.stream({"messages": messages}, stream_mode=["updates", "custom"]):
        if mode == "custom" and chunk.get("observer"):
            event_type = chunk.get("event")
            data = chunk.get("data")
            ev = observer.record(event_type, data)
            writer.write(ev)
        elif mode == "updates":
            for update in chunk.values():
                if isinstance(update, dict) and update.get("messages"):
                    messages.extend(update["messages"])

    ev_done = observer.record("run_completed", {})
    writer.write(ev_done)
    observer.sync_messages(messages)
    print(f"Recorded trace: {writer.path.name}")
    return writer.path


def main():
    # -------------------------------------------------------------
    # Case A: Mua 28/09/2026, yêu cầu 06/10/2026, chưa kích hoạt
    # -------------------------------------------------------------
    conv_a = uuid.uuid4().hex
    prompt_a = "Tôi mua ngày 28/09/2026, yêu cầu hoàn ngày 06/10/2026, chưa kích hoạt. Tôi có được hoàn không?"
    responses_a = [
        AIMessage(
            content="",
            tool_calls=[{"name": "read_file", "args": {"path": "skills/refund-policy/SKILL.md"}, "id": "call_skill_a"}],
        ),
        AIMessage(
            content="",
            tool_calls=[
                {"name": "list_files", "args": {"path": "data/policies"}, "id": "call_list_a"},
                {"name": "read_file", "args": {"path": "skills/refund-policy/references/answer-template.md"}, "id": "call_tpl_a"},
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[{"name": "read_file", "args": {"path": "data/policies/policy-before-oct.md"}, "id": "call_policy_a"}],
        ),
        AIMessage(
            content=(
                "- **Chính sách áp dụng:** Chính sách hoàn tiền trước tháng 10 (áp dụng cho ngày mua trước 2026-10-01)\n"
                "- **Thời gian:** Ngày mua: 28/09/2026, Ngày yêu cầu: 06/10/2026 (Chênh lệch: 8 ngày)\n"
                "- **Trạng thái kích hoạt:** Chưa kích hoạt\n"
                "- **Kết luận:** Không đủ điều kiện hoàn tiền (Thời hạn yêu cầu hoàn tiền là trong vòng 7 ngày kể từ ngày mua, bạn đã yêu cầu sau 8 ngày nên đã quá hạn)\n"
                "- **Phí hoàn tiền:** Không áp dụng do không đủ điều kiện hoàn tiền\n"
                "- **Căn cứ tài liệu:** data/policies/policy-before-oct.md"
            )
        ),
    ]
    run_simulated_turn(prompt_a, responses_a, conv_a, 1)

    # -------------------------------------------------------------
    # Case B sau khi đổi tên file:
    # Đổi tên file trong workspace/data/policies:
    # policy-before-oct.md -> chinh-sach-cu.md
    # policy-from-oct.md -> chinh-sach-moi.md
    # -------------------------------------------------------------
    policies_dir = paths.WORKSPACE_DIR / "data" / "policies"
    f_before = policies_dir / "policy-before-oct.md"
    f_from = policies_dir / "policy-from-oct.md"
    renamed_before = policies_dir / "chinh-sach-cu.md"
    renamed_from = policies_dir / "chinh-sach-moi.md"

    if f_before.exists():
        f_before.rename(renamed_before)
    if f_from.exists():
        f_from.rename(renamed_from)

    conv_b = uuid.uuid4().hex
    prompt_b = "Tôi mua ngày 02/10/2026, yêu cầu hoàn ngày 12/10/2026, chưa kích hoạt. Tôi có được hoàn không?"
    responses_b = [
        AIMessage(
            content="",
            tool_calls=[{"name": "read_file", "args": {"path": "skills/refund-policy/SKILL.md"}, "id": "call_skill_b"}],
        ),
        AIMessage(
            content="",
            tool_calls=[
                {"name": "list_files", "args": {"path": "data/policies"}, "id": "call_list_b"},
                {"name": "read_file", "args": {"path": "skills/refund-policy/references/answer-template.md"}, "id": "call_tpl_b"},
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[{"name": "read_file", "args": {"path": "data/policies/chinh-sach-moi.md"}, "id": "call_policy_b"}],
        ),
        AIMessage(
            content=(
                "- **Chính sách áp dụng:** Chính sách hoàn tiền từ tháng 10 (áp dụng cho ngày mua từ 2026-10-01, bao gồm ngày này)\n"
                "- **Thời gian:** Ngày mua: 02/10/2026, Ngày yêu cầu: 12/10/2026 (Chênh lệch: 10 ngày)\n"
                "- **Trạng thái kích hoạt:** Chưa kích hoạt\n"
                "- **Kết luận:** Đủ điều kiện hoàn tiền (Thời gian yêu cầu 10 ngày nằm trong thời hạn 14 ngày cho phép và sản phẩm chưa kích hoạt)\n"
                "- **Phí hoàn tiền:** Không thu phí hoàn tiền\n"
                "- **Căn cứ tài liệu:** data/policies/chinh-sach-moi.md"
            )
        ),
    ]
    run_simulated_turn(prompt_b, responses_b, conv_b, 1)

    # Đổi lại tên và giữ cả hai bản để sau này kiểm tra
    if renamed_before.exists():
        f_before.write_text(renamed_before.read_text(encoding="utf-8"), encoding="utf-8")
    if renamed_from.exists():
        f_from.write_text(renamed_from.read_text(encoding="utf-8"), encoding="utf-8")

    # -------------------------------------------------------------
    # Case Thiếu thông tin:
    # -------------------------------------------------------------
    conv_c = uuid.uuid4().hex
    prompt_c = "Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026."
    responses_c = [
        AIMessage(
            content="",
            tool_calls=[{"name": "read_file", "args": {"path": "skills/refund-policy/SKILL.md"}, "id": "call_skill_c"}],
        ),
        AIMessage(
            content=(
                "Để xác định chính xác bạn có đủ điều kiện hoàn tiền hay không, vui lòng cho biết thêm:\n"
                "Sản phẩm của bạn **đã được kích hoạt hay chưa**?\n\n"
                "Theo quy định chính sách hoàn tiền, nếu sản phẩm đã kích hoạt thì sẽ không được hoàn tiền bất kể thời gian mua hàng."
            )
        ),
    ]
    run_simulated_turn(prompt_c, responses_c, conv_c, 1)


if __name__ == "__main__":
    main()
