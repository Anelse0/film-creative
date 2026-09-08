#!/usr/bin/env bash
# 回归测试：校验脚本对示例文件的预期结果。任何一项不符即失败。
set -u
cd "$(dirname "$0")/.."
fail=0
check() { # name, condition-expression-result(0/1), detail
  if [ "$2" -eq 0 ]; then echo "PASS $1"; else echo "FAIL $1 — $3"; fail=1; fi
}

C="python3 scripts/validate_concept.py"
out=$($C examples/good-concept.md); rc=$?
check "good-concept exits 0" $rc "$out"
echo "$out" | grep -q "0 error(s), 0 warning(s)"; check "good-concept clean (single candidate, research rows with 可信范围)" $? "$(echo "$out" | tail -1)"
out=$($C examples/bad-concept.md); rc=$?
[ $rc -eq 1 ]; check "bad-concept exits 1" $? "rc=$rc"
for code in C03 C04 C06 C07 C10 C11; do
  echo "$out" | grep -q "$code"; check "bad-concept has $code" $? ""
done
# 2.4.0: 候选数量不固定；集中研究一个题材不是错误；旧格式概念卡只告警不报错
out=$($C tests/fixtures/concept-legacy-2.3.md); rc=$?
check "legacy 2.3 concept card exits 0" $rc "$out"
echo "$out" | grep -q "C07"; check "legacy card now warns about research record columns" $? "$out"
echo "$out" | grep -q "候选只有\|需要 3"; rc=$?
[ "$rc" -ne 0 ]; check "no fixed candidate count" $? "$out"
grep -q "^## 工作示例\|^## 附：骰子" references/concept-generation.md && { echo "FAIL concept-generation.md 仍含工作示例正文"; fail=1; } || echo "PASS concept-generation.md has no worked examples"

# 结构：保留已安装的调用名称（目录大小写可以不同）
grep -q "^name: film-creative" SKILL.md; check "SKILL.md invocation name preserved" $? ""
# 所有 SKILL.md 引用的 references/templates 文件存在
missing=""
for f in $(grep -oE '`(references|templates|scripts|examples)/[^`]+`' SKILL.md | tr -d '`' | sort -u); do
  [ -e "$f" ] || missing="$missing $f"
done
[ -z "$missing" ]; check "SKILL.md links resolve" $? "$missing"

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
check "creative regression suite" $? ""
exit $fail
