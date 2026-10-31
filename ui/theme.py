"""
ui/theme.py
===========
Design system tokens — all colors, fonts, and dimension constants
for the futuristic glassmorphism UI.

Edit this file to retheme the entire application.
"""

# ---------------------------------------------------------------------------
# Transparency key
# A near-black color used as the Windows transparent-color key so the
# floating widget appears as a true circle (non-rectangular window).
# ---------------------------------------------------------------------------
TRANSPARENT_KEY = '#010203'

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
COLORS = {
    # ── Core Backgrounds ───────────────────────────────────────────────────
    'transparent':          '#010203',   # window transparency key
    'bg_root':              '#050810',   # deepest background
    'bg_panel':             '#080f1e',   # main panel background
    'bg_header':            '#060c18',   # header / footer strips
    'bg_glass':             '#0a1628',   # glass card background
    'bg_glass_light':       '#0f1e38',   # lighter glass variant
    'bg_input':             '#060d1a',   # input field background

    # ── Borders & Glow ────────────────────────────────────────────────────
    'border_subtle':        '#1a2d4a',   # subtle divider
    'border_mid':           '#243d60',   # mid-strength border
    'border_cyan_glow':     '#00d4ff',   # cyan glowing border
    'border_violet_glow':   '#7c3aed',   # violet glowing border
    'border_green_glow':    '#00ff88',   # green glowing border

    # ── Accent Colors ─────────────────────────────────────────────────────
    'accent_cyan':          '#00d4ff',   # primary accent
    'accent_cyan_soft':     '#00aacc',   # softer cyan
    'accent_cyan_dim':      '#00334d',   # very dim cyan (glow background)
    'accent_violet':        '#7c3aed',   # secondary accent
    'accent_violet_soft':   '#9f5cf0',   # lighter violet
    'accent_violet_dim':    '#2a0d5e',   # dim violet
    'accent_green':         '#00ff88',   # assistant / success
    'accent_green_soft':    '#00cc6a',   # softer green
    'accent_green_dim':     '#003322',   # dim green
    'accent_red':           '#ff4466',   # error / danger
    'accent_yellow':        '#ffd700',   # warning / busy

    # ── Text ──────────────────────────────────────────────────────────────
    'text_primary':         '#e2e8f0',   # main body text
    'text_secondary':       '#94a3b8',   # secondary / dimmed text
    'text_muted':           '#475569',   # very muted (timestamps, hints)
    'text_accent':          '#00d4ff',   # accent text (AI name, labels)
    'text_green':           '#00ff88',   # success / assistant name

    # ── Message Bubbles ───────────────────────────────────────────────────
    'bubble_user_bg':       '#0a1e3a',   # user message background
    'bubble_user_border':   '#00d4ff',   # user message border
    'bubble_asst_bg':       '#071a10',   # assistant message background
    'bubble_asst_border':   '#00ff88',   # assistant message border
    'bubble_sys_bg':        '#1a0e2e',   # system message background
    'bubble_sys_border':    '#7c3aed',   # system message border

    # ── Buttons ───────────────────────────────────────────────────────────
    'btn_primary_bg':       '#00d4ff',   # filled primary button
    'btn_primary_fg':       '#020810',   # text on filled button
    'btn_primary_hover':    '#00aacc',   # hover state
    'btn_ghost_bg':         '#0a1628',   # ghost / outline button bg
    'btn_ghost_fg':         '#00d4ff',   # ghost button text/border
    'btn_ghost_hover':      '#0f1e38',   # ghost hover bg
    'btn_close_hover':      '#3d0a14',   # close button hover

    # ── Status Indicators ─────────────────────────────────────────────────
    'status_ready':         '#00ff88',   # online / ready (green)
    'status_busy':          '#ffd700',   # processing (yellow)
    'status_error':         '#ff4466',   # error (red)
    'status_offline':       '#475569',   # offline (gray)

    # ── Floating Orb ──────────────────────────────────────────────────────
    'orb_bg':               '#070e1c',   # orb circle fill
    'orb_inner':            '#0a1628',   # orb inner layer
    'orb_glow_base':        '#001a2a',   # outer glow base color
    'orb_node':             '#00d4ff',   # neural network node fill
    'orb_line':             '#004466',   # neural network connector

    # ── Scrollbar ─────────────────────────────────────────────────────────
    'scrollbar_bg':         '#080f1e',
    'scrollbar_thumb':      '#1e3a5f',
    'scrollbar_thumb_hover':'#00d4ff',
}

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
FONTS = {
    'title':        ('Segoe UI', 12, 'bold'),
    'header':       ('Segoe UI', 11, 'bold'),
    'subheader':    ('Segoe UI', 9),
    'body':         ('Segoe UI', 10),
    'body_bold':    ('Segoe UI', 10, 'bold'),
    'small':        ('Segoe UI', 8),
    'small_bold':   ('Segoe UI', 8, 'bold'),
    'tiny':         ('Segoe UI', 7),
    'mono':         ('Consolas', 9),
    'mono_small':   ('Consolas', 8),
    'btn':          ('Segoe UI', 9, 'bold'),
    'btn_small':    ('Segoe UI', 8, 'bold'),
    'timestamp':    ('Segoe UI', 7),
    'orb':          ('Segoe UI', 8, 'bold'),
    'quick_btn':    ('Segoe UI', 8),
}

# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------

# Floating orb widget
WIDGET_W = 80        # orb window width  (px)
WIDGET_H = 80        # orb window height (px)
ORB_RADIUS = 32      # circle radius drawn on canvas

# Main chat panel
PANEL_W = 420        # panel window width  (px)
PANEL_H = 660        # panel window height (px)
PANEL_CORNER = 16    # panel corner radius for glass background

# Chat area
MSG_MAX_WIDTH = 300  # max message bubble width (px)
MSG_PAD_X = 12       # bubble horizontal padding
MSG_PAD_Y = 8        # bubble vertical padding
BUBBLE_CORNER = 10   # bubble corner radius

# Header
HEADER_H = 52        # header bar height (px)

# Quick actions row
QA_H = 44            # quick-action row height (px)

# Input bar
INPUT_H = 56         # input bar height (px)

# Glow animation
GLOW_LAYERS = 5      # number of concentric glow rings on orb
GLOW_MIN = 0.15      # minimum glow intensity
GLOW_MAX = 0.75      # maximum glow intensity

# Typing indicator
TYPING_DOTS = 3      # number of bouncing dots
TYPING_DOT_R = 4     # dot radius (px)
TYPING_DOT_GAP = 10  # gap between dots (px)
