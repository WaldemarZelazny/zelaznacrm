"""Generate improved ERD.png for ZelaznaCRM — 4x3 grid layout, A3 landscape."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

# ---------------------------------------------------------------------------
# Model definitions: (name, col, row, pk_fields, fk_fields, plain_fields, color)
# Grid positions: col 0-3, row 0-2 (top to bottom)
# ---------------------------------------------------------------------------
MODELS = [
    # Row 0
    (
        "User",
        0,
        0,
        ["id"],
        [],
        ["username", "first_name", "last_name", "email", "is_active", "is_staff"],
        "#4e79a7",
        "django.contrib.auth",
    ),
    (
        "UserProfile",
        1,
        0,
        ["id"],
        ["user_id → User"],
        ["role", "phone", "avatar", "created_at"],
        "#59a14f",
        "accounts",
    ),
    (
        "Company",
        2,
        0,
        ["id"],
        ["owner_id → User"],
        ["name", "nip", "city", "industry", "phone", "email", "is_active"],
        "#f28e2b",
        "companies",
    ),
    (
        "Contact",
        3,
        0,
        ["id"],
        ["company_id → Company", "owner_id → User"],
        ["first_name", "last_name", "email", "phone", "department", "is_active"],
        "#e15759",
        "contacts",
    ),
    # Row 1
    (
        "WorkflowStage",
        0,
        1,
        ["id"],
        [],
        ["name", "order", "color", "is_active"],
        "#76b7b2",
        "leads",
    ),
    (
        "Lead",
        1,
        1,
        ["id"],
        [
            "company_id → Company",
            "contact_id → Contact",
            "owner_id → User",
            "stage_id → WorkflowStage",
        ],
        ["title", "status", "source", "value", "created_at"],
        "#edc948",
        "leads",
    ),
    (
        "Deal",
        2,
        1,
        ["id"],
        ["company_id → Company", "lead_id → Lead", "owner_id → User"],
        ["title", "status", "value", "close_date", "created_at"],
        "#b07aa1",
        "deals",
    ),
    (
        "Task",
        3,
        1,
        ["id"],
        [
            "company_id → Company",
            "lead_id → Lead",
            "deal_id → Deal",
            "assigned_to → User",
        ],
        ["title", "task_type", "priority", "status", "due_date"],
        "#ff9da7",
        "tasks",
    ),
    # Row 2
    (
        "Document",
        0,
        2,
        ["id"],
        [
            "company_id → Company",
            "lead_id → Lead",
            "deal_id → Deal",
            "created_by → User",
        ],
        ["title", "doc_type", "file", "created_at"],
        "#9c755f",
        "documents",
    ),
    (
        "Note",
        1,
        2,
        ["id"],
        [
            "author_id → User",
            "company_id → Company",
            "lead_id → Lead",
            "deal_id → Deal",
        ],
        ["content", "created_at"],
        "#bab0ac",
        "notes",
    ),
    (
        "ActivityLog",
        2,
        2,
        ["id"],
        ["user_id → User"],
        [
            "action",
            "model_name",
            "object_id",
            "object_repr",
            "ip_address",
            "created_at",
        ],
        "#86bcb6",
        "reports",
    ),
]

# Key relationships to draw as arrows (src_model, dst_model, label)
RELATIONS = [
    ("User", "UserProfile", "1:1"),
    ("User", "Company", "1:N"),
    ("Company", "Contact", "1:N"),
    ("Company", "Lead", "1:N"),
    ("Lead", "Deal", "1:N"),
    ("Lead", "Task", "0:N"),
    ("Deal", "Document", "0:N"),
    ("WorkflowStage", "Lead", "1:N"),
    ("Contact", "Lead", "0:N"),
]

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
FIG_W, FIG_H = 24, 18
COLS, ROWS = 4, 3
CELL_W = FIG_W / COLS  # 6.0 inches per cell
CELL_H = FIG_H / ROWS  # 6.0 inches per cell
MARGIN_X = 0.35  # horizontal margin within cell (inches)
MARGIN_Y = 0.45  # vertical margin within cell (inches)
BOX_W = CELL_W - 2 * MARGIN_X
HEADER_H = 0.55
PK_H = 0.35
FK_H = 0.32
PLAIN_H = 0.30
SECTION_GAP = 0.08

FONT_HEADER = 12
FONT_SECTION = 8.5
FONT_FIELD = 9.5

COLOR_PK_BG = "#f0f0f0"
COLOR_FK_BG = "#fafafa"
COLOR_PLAIN_BG = "#ffffff"
COLOR_SECTION_LABEL = "#888888"

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
ax.set_facecolor("#f4f6fb")
fig.patch.set_facecolor("#f4f6fb")

model_boxes = {}  # name → (cx, cy, left, right, top, bottom)


def draw_box(ax, name, col, row, pk_fields, fk_fields, plain_fields, color):
    """Draw one model box and return anchor points."""
    # Cell origin (matplotlib Y grows upward, so row 0 = top)
    cell_x = col * CELL_W
    cell_y = FIG_H - (row + 1) * CELL_H  # bottom of cell in figure coords

    box_x = cell_x + MARGIN_X
    # calculate total height
    total_h = (
        HEADER_H
        + (SECTION_GAP + PK_H * len(pk_fields) if pk_fields else 0)
        + (SECTION_GAP + FK_H * len(fk_fields) if fk_fields else 0)
        + (SECTION_GAP + PLAIN_H * len(plain_fields) if plain_fields else 0)
        + 0.12  # bottom padding
    )
    # Center box vertically in cell
    box_y_bottom = cell_y + (CELL_H - total_h) / 2
    box_y_top = box_y_bottom + total_h

    # --- Header ---
    header = FancyBboxPatch(
        (box_x, box_y_top - HEADER_H),
        BOX_W,
        HEADER_H,
        boxstyle="round,pad=0.03",
        linewidth=1.6,
        edgecolor="#333",
        facecolor=color,
        zorder=4,
        clip_on=False,
    )
    ax.add_patch(header)
    ax.text(
        box_x + BOX_W / 2,
        box_y_top - HEADER_H / 2,
        name,
        ha="center",
        va="center",
        fontsize=FONT_HEADER,
        fontweight="bold",
        color="white",
        zorder=5,
    )

    cursor_y = box_y_top - HEADER_H

    def draw_section(fields, bg_color, prefix, font_bold=False, row_h=PLAIN_H):
        nonlocal cursor_y
        if not fields:
            return
        cursor_y -= SECTION_GAP
        sec_h = row_h * len(fields)
        sec_box = FancyBboxPatch(
            (box_x, cursor_y - sec_h),
            BOX_W,
            sec_h,
            boxstyle="round,pad=0.02",
            linewidth=1.0,
            edgecolor="#cccccc",
            facecolor=bg_color,
            zorder=3,
            clip_on=False,
        )
        ax.add_patch(sec_box)
        for i, field in enumerate(fields):
            fy = cursor_y - (i + 0.52) * row_h
            ax.text(
                box_x + 0.14,
                fy,
                prefix + field,
                ha="left",
                va="center",
                fontsize=FONT_FIELD,
                fontweight="bold" if font_bold else "normal",
                color="#111111" if font_bold else "#333333",
                zorder=5,
                family="monospace",
                clip_on=False,
            )
        cursor_y -= sec_h

    draw_section(pk_fields, COLOR_PK_BG, "PK  ", font_bold=True, row_h=PK_H)
    draw_section(fk_fields, COLOR_FK_BG, "FK  ", row_h=FK_H)
    draw_section(plain_fields, COLOR_PLAIN_BG, "    ", row_h=PLAIN_H)

    # Outer border
    border = FancyBboxPatch(
        (box_x, box_y_bottom),
        BOX_W,
        total_h,
        boxstyle="round,pad=0.03",
        linewidth=1.8,
        edgecolor="#555555",
        facecolor="none",
        zorder=6,
        clip_on=False,
    )
    ax.add_patch(border)

    cx = box_x + BOX_W / 2
    cy = box_y_bottom + total_h / 2
    model_boxes[name] = dict(
        cx=cx,
        cy=cy,
        left=box_x,
        right=box_x + BOX_W,
        top=box_y_top,
        bottom=box_y_bottom,
    )


for name, col, row, pk_fields, fk_fields, plain_fields, color, _app in MODELS:
    draw_box(ax, name, col, row, pk_fields, fk_fields, plain_fields, color)


def nearest_edge(src, dst):
    """Return (sx, sy, dx, dy) connecting closest edges of two boxes."""
    s = model_boxes[src]
    d = model_boxes[dst]
    # Determine dominant direction
    dx = d["cx"] - s["cx"]
    dy = d["cy"] - s["cy"]
    if abs(dx) >= abs(dy):
        # horizontal connection
        if dx > 0:
            return s["right"], s["cy"], d["left"], d["cy"]
        else:
            return s["left"], s["cy"], d["right"], d["cy"]
    else:
        # vertical connection
        if dy > 0:
            return s["cx"], s["top"], d["cx"], d["bottom"]
        else:
            return s["cx"], s["bottom"], d["cx"], d["top"]


for src, dst, label in RELATIONS:
    if src not in model_boxes or dst not in model_boxes:
        continue
    sx, sy, dx, dy = nearest_edge(src, dst)
    ax.annotate(
        "",
        xy=(dx, dy),
        xytext=(sx, sy),
        arrowprops=dict(
            arrowstyle="-|>",
            color="#666666",
            lw=1.0,
            shrinkA=4,
            shrinkB=4,
            connectionstyle="arc3,rad=0.06",
        ),
        zorder=2,
    )
    mid_x = (sx + dx) / 2
    mid_y = (sy + dy) / 2
    ax.text(
        mid_x,
        mid_y + 0.06,
        label,
        fontsize=8.5,
        color="#444444",
        ha="center",
        va="center",
        bbox=dict(fc="white", ec="none", alpha=0.88, pad=2),
        zorder=7,
    )

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
ax.text(
    FIG_W / 2,
    FIG_H - 0.22,
    "ZelaznaCRM — Diagram ERD (Entity-Relationship Diagram)",
    ha="center",
    va="center",
    fontsize=16,
    fontweight="bold",
    color="#1a1a2e",
)
ax.text(
    FIG_W / 2,
    FIG_H - 0.52,
    "Django 6.x  |  11 modeli  |  9 aplikacji  |  Kwiecień 2026",
    ha="center",
    va="center",
    fontsize=10,
    color="#555555",
)

# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
legend_items = [
    mpatches.Patch(color=color, label=f"{app}  ({name})")
    for name, _col, _row, _pk, _fk, _pl, color, app in MODELS
]
ax.legend(
    handles=legend_items,
    loc="lower right",
    fontsize=9,
    framealpha=0.95,
    ncol=2,
    bbox_to_anchor=(1.0, 0.0),
    title="Aplikacje Django",
    title_fontsize=10,
)

# ---------------------------------------------------------------------------
# Section legend (top-left)
# ---------------------------------------------------------------------------
for i, (lbl, bg) in enumerate(
    [
        ("PK  — klucz główny", COLOR_PK_BG),
        ("FK  — klucz obcy", COLOR_FK_BG),
        ("       — pole zwykłe", COLOR_PLAIN_BG),
    ]
):
    ry = FIG_H - 0.85 - i * 0.32
    ax.add_patch(
        FancyBboxPatch(
            (0.25, ry - 0.13),
            0.22,
            0.24,
            boxstyle="round,pad=0.02",
            linewidth=0.8,
            edgecolor="#aaa",
            facecolor=bg,
            zorder=3,
        )
    )
    ax.text(0.54, ry, lbl, fontsize=8.5, va="center", color="#333", family="monospace")

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig("ERD.png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
print("Saved: ERD.png")
