#!/usr/bin/env python3
"""
自作アコーディオンコンポーネント - Flet 0.21.0+ 対応版
UserControl非推奨のため関数型実装
"""

import flet as ft


def make_accordion(page: ft.Page,
                   items: list[tuple[str, ft.Control, bool]],
                   single_open: bool = True,
                   spacing: int = 8,
                   header_bg = ft.Colors.TRANSPARENT,
                   body_bg   = ft.Colors.TRANSPARENT,
                   radius: int = 10) -> ft.Column:
    """
    関数型アコーディオン作成（UserControl非推奨対応）
    
    Args:
        page: Fletページ（update用）
        items: [(title, content_control, initially_expanded), ...]
        single_open: 単一展開モード
        spacing: 項目間スペース
        header_bg: ヘッダー背景色
        body_bg: ボディ背景色
        radius: 角丸半径
        
    Returns:
        ft.Column: そのまま page.add(...) で使えるコンポーネント
    """
    rows: list[ft.Control] = []
    states: list[dict] = []
    refs: list[dict] = []

    def set_open(i: int, open_: bool):
        """指定項目の開閉状態設定"""
        st   = states[i]
        chev = refs[i]["chev"].current
        body = refs[i]["body"].current

        st["expanded"] = open_
        # アイコン回転
        chev.rotate = ft.Rotate(angle=1.5708 if open_ else 0.0)
        # ボディ開閉
        if open_:
            body.visible = True
            body.height  = None  # 自動高さ
        else:
            body.height  = 0
            body.visible = False

    def on_header_click(i: int):
        """ヘッダークリックハンドラ生成"""
        def handler(_):
            now = states[i]["expanded"]
            set_open(i, not now)

            if single_open and (not now):
                # 自分を開いたら他は閉じる
                for j in range(len(states)):
                    if j != i and states[j]["expanded"]:
                        set_open(j, False)
            page.update()
        return handler

    # 各項目作成
    for idx, (title, body_control, initially) in enumerate(items):
        chev_ref = ft.Ref[ft.Icon]()
        body_ref = ft.Ref[ft.Container]()

        # ヘッダー
        header = ft.Container(
            bgcolor=header_bg,
            border_radius=ft.border_radius.only(top_left=radius, top_right=radius),
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            on_click=on_header_click(idx),
            content=ft.Row(
                [
                    ft.Text(title, weight=ft.FontWeight.W_600),
                    ft.Container(expand=True),  # spacer
                    ft.Icon(
                        name=ft.Icons.KEYBOARD_ARROW_RIGHT_ROUNDED,
                        ref=chev_ref,
                        rotate=ft.Rotate(angle=1.5708 if initially else 0.0),
                        animate_rotation=ft.Animation(200, "easeOut"),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # ボディ
        body = ft.Container(
            ref=body_ref,
            content=body_control,
            bgcolor=body_bg,
            border_radius=ft.border_radius.only(bottom_left=radius, bottom_right=radius),
            padding=ft.padding.only(left=12, right=12, bottom=10),
            animate_size=ft.Animation(200, "easeOut"),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,  # はみ出し/線防止
        )
        
        # 初期状態反映
        if not initially:
            body.height = 0
            body.visible = False

        rows.append(ft.Column([header, body], spacing=0))
        states.append({"expanded": initially})
        refs.append({"chev": chev_ref, "body": body_ref})

    return ft.Column(rows, spacing=spacing)


def create_ocr_detail_accordion(page: ft.Page, accordion_items: list[tuple[str, ft.Control, bool]]) -> ft.Column:
    """OCR詳細設定用の複数アコーディオン作成"""
    return make_accordion(
        page=page,
        items=accordion_items,
        single_open=False,  # 複数開閉可能
        spacing=6,
        header_bg=ft.Colors.BLUE_GREY_50,   # 薄いグレー（ユーザー要求）
        body_bg=ft.Colors.TRANSPARENT,      # 内容は透過
        radius=0                            # 角丸なし（ユーザー要求）
    )


def create_ocr_accordion_item(page: ft.Page, title: str, controls: list[ft.Control], initially_expanded: bool = True) -> ft.Control:
    """OCR設定用アコーディオン項目作成（関数型）"""
    content = ft.Column(controls, spacing=4, tight=True)
    
    accordion = make_accordion(
        page=page,
        items=[(title, content, initially_expanded)],
        single_open=False,  # 単独項目なので無効
        header_bg=ft.Colors.BLUE_50,
        body_bg=ft.Colors.WHITE,
        spacing=4
    )
    
    return accordion


def create_ocr_multi_accordion(page: ft.Page, sections: list[tuple[str, list[ft.Control], bool]]) -> ft.Control:
    """OCR設定用複数セクションアコーディオン作成"""
    items = []
    for title, controls, initially_expanded in sections:
        content = ft.Column(controls, spacing=4, tight=True)
        items.append((title, content, initially_expanded))
    
    return make_accordion(
        page=page,
        items=items,
        single_open=True,  # 単一展開モード
        header_bg=ft.Colors.BLUE_50,
        body_bg=ft.Colors.WHITE,
        spacing=8
    )