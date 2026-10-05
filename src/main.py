import sys
from array import array
from typing import Sequence, TypeVar

T = TypeVar("T")


def read_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def split_lines(data: bytes) -> list[bytes]:
    if not data:
        return []
    if data.endswith(b"\n"):
        data = data[:-1]
    return data.split(b"\n")


def order_change_blocks(operations: list[tuple[str, T]]) -> list[tuple[str, T]]:
    result: list[tuple[str, T]] = []
    i = 0
    n = len(operations)
    while i < n:
        if operations[i][0] == "keep":
            result.append(operations[i])
            i += 1
        else:
            deletes: list[tuple[str, T]] = []
            inserts: list[tuple[str, T]] = []
            while i < n and operations[i][0] != "keep":
                if operations[i][0] == "delete":
                    deletes.append(operations[i])
                else:
                    inserts.append(operations[i])
                i += 1
            result.extend(deletes)
            result.extend(inserts)
    return result


def backtrack(
    trace: list[array],
    a: Sequence[T],
    b: Sequence[T],
    d: int,
    k: int,
) -> list[tuple[str, T]]:
    x = len(a)
    y = len(b)
    ops: list[tuple[str, T]] = []

    for step in range(d, 0, -1):
        v_prev = trace[step - 1]

        if k == -step:
            prev_k = k + 1
        elif k == step:
            prev_k = k - 1
        else:
            left = v_prev[(k - 1 + step - 1) // 2]
            right = v_prev[(k + 1 + step - 1) // 2]

            if left < right:
                prev_k = k + 1
            else:
                prev_k = k - 1

        start_x = v_prev[(prev_k + step - 1) // 2]
        start_y = start_x - prev_k

        if prev_k == k + 1:
            mid_x = start_x
            mid_y = start_y + 1
        else:
            mid_x = start_x + 1
            mid_y = start_y

        while x > mid_x and y > mid_y:
            x -= 1
            y -= 1
            ops.append(("keep", a[x]))

        if prev_k == k + 1:
            ops.append(("insert", b[start_y]))
        else:
            ops.append(("delete", a[start_x]))

        x = start_x
        y = start_y
        k = prev_k

    while x > 0 and y > 0:
        x -= 1
        y -= 1
        ops.append(("keep", a[x]))

    ops.reverse()
    return order_change_blocks(ops)


def myers_diff(a: Sequence[T], b: Sequence[T]) -> list[tuple[str, T]]:
    n = len(a)
    m = len(b)
    max_d = n + m

    x = 0
    y = 0

    while x < n and y < m and a[x] == b[y]:
        x += 1
        y += 1

    trace: list[array] = [array("i", [x])]

    if x >= n and y >= m:
        return [("keep", a[i]) for i in range(n)]

    previous = trace[0]

    for d in range(1, max_d + 1):
        current = array("i", [0]) * (d + 1)

        for index, k in enumerate(range(-d, d + 1, 2)):
            if k == -d:
                x = previous[0]
            elif k == d:
                x = previous[-1] + 1
            else:
                left = previous[(k - 1 + d - 1) // 2]
                right = previous[(k + 1 + d - 1) // 2]

                if left < right:
                    x = right
                else:
                    x = left + 1

            y = x - k

            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            current[index] = x

            if x >= n and y >= m:
                trace.append(current)
                return backtrack(trace, a, b, d, k)

        trace.append(current)
        previous = current

    return []


def format_ranges(indices: list[int]) -> str:
    if not indices:
        return "."
    ranges: list[str] = []
    start = indices[0]
    end = start + 1
    for pos in indices[1:]:
        if pos == end:
            end += 1
        else:
            ranges.append(f"{start}-{end}")
            start = pos
            end = pos + 1
    ranges.append(f"{start}-{end}")
    return ",".join(ranges)


def compute_changed_ranges(old_str: str, new_str: str) -> tuple[str, str]:
    char_diff = myers_diff(list(old_str), list(new_str))
    old_indices: list[int] = []
    new_indices: list[int] = []
    old_pos = 0
    new_pos = 0

    for op, _ in char_diff:
        if op == "keep":
            old_pos += 1
            new_pos += 1
        elif op == "delete":
            old_indices.append(old_pos)
            old_pos += 1
        elif op == "insert":
            new_indices.append(new_pos)
            new_pos += 1

    return format_ranges(old_indices), format_ranges(new_indices)


def pair_change_blocks(
    diff: list[tuple[str, bytes]],
) -> list[tuple[str, bytes, str | None]]:
    result: list[tuple[str, bytes, str | None]] = []
    i = 0
    n = len(diff)
    while i < n:
        if diff[i][0] == "keep":
            result.append(("keep", diff[i][1], None))
            i += 1
        else:
            deletes: list[bytes] = []
            inserts: list[bytes] = []
            while i < n and diff[i][0] != "keep":
                if diff[i][0] == "delete":
                    deletes.append(diff[i][1])
                else:
                    inserts.append(diff[i][1])
                i += 1

            pair_count = min(len(deletes), len(inserts))
            pairs: list[tuple[str, str]] = []
            for j in range(pair_count):
                old_str = deletes[j].decode("utf-8")
                new_str = inserts[j].decode("utf-8")
                pairs.append(compute_changed_ranges(old_str, new_str))

            for j, d_line in enumerate(deletes):
                rng = pairs[j][0] if j < pair_count else None
                result.append(("delete", d_line, rng))

            for j, i_line in enumerate(inserts):
                rng = pairs[j][1] if j < pair_count else None
                result.append(("insert", i_line, rng))

    return result


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A_PATH B_PATH", file=sys.stderr)
        return 2
    command, a_path, b_path = sys.argv[1:]
    try:
        a_bytes = read_file(a_path)
        b_bytes = read_file(b_path)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    a_lines = split_lines(a_bytes)
    b_lines = split_lines(b_bytes)
    diff = myers_diff(a_lines, b_lines)

    if command == "lines":
        out = []
        for op, line in diff:
            prefix = b" " if op == "keep" else (b"-" if op == "delete" else b"+")
            out.append(prefix + line + b"\n")
        sys.stdout.buffer.write(b"".join(out))
    elif command == "highlight":
        paired = pair_change_blocks(diff)
        out = []
        pending_old_ranges: list[str] = []
        pending_index = 0
        for op, line, rng in paired:
            if op == "keep":
                out.append(b" " + line + b"\n")
            elif op == "delete":
                out.append(b"-" + line + b"\n")
                if rng is not None:
                    pending_old_ranges.append(rng)
            elif op == "insert":
                out.append(b"+" + line + b"\n")
                if rng is not None:
                    old_rng = pending_old_ranges[pending_index]
                    pending_index += 1
                    out.append(f"? {old_rng} | {rng}\n".encode("utf-8"))
        sys.stdout.buffer.write(b"".join(out))

    return 0


raise SystemExit(main())
