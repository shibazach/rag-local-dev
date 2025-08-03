"""
フォームコンポーネント
Reusable form components with validation and styling
"""

from nicegui import ui
from typing import Optional, List, Dict, Any, Callable
from app.ui.themes.base import RAGTheme

class RAGInput:
    """統一入力フィールドコンポーネント"""
    
    def __init__(
        self,
        label: str,
        placeholder: str = "",
        value: str = "",
        input_type: str = "text",
        required: bool = False,
        validation: Optional[Callable] = None,
        on_change: Optional[Callable] = None,
        disabled: bool = False,
        error_message: str = ""
    ):
        self.label = label
        self.placeholder = placeholder
        self.value = value
        self.input_type = input_type
        self.required = required
        self.validation = validation
        self.on_change = on_change
        self.disabled = disabled
        self.error_message = error_message
        
        self.input_element = self._create_input()
    
    def _create_input(self):
        """入力フィールド作成"""
        with ui.column().classes('w-full mb-4'):
            # ラベル
            label_classes = 'block text-sm font-medium text-gray-700 mb-1'
            if self.required:
                ui.label(f'{self.label} *').classes(label_classes + ' text-red-600')
            else:
                ui.label(self.label).classes(label_classes)
            
            # 入力フィールド
            if self.input_type == "password":
                input_element = ui.input(
                    placeholder=self.placeholder,
                    value=self.value,
                    password=True,
                    on_change=self._handle_change
                ).classes('rag-input w-full')
            elif self.input_type == "email":
                input_element = ui.input(
                    placeholder=self.placeholder,
                    value=self.value,
                    validation={'Email': lambda value: '@' in value},
                    on_change=self._handle_change
                ).classes('rag-input w-full')
            elif self.input_type == "number":
                input_element = ui.number(
                    placeholder=self.placeholder,
                    value=float(self.value) if self.value else None,
                    on_change=self._handle_change
                ).classes('rag-input w-full')
            else:
                input_element = ui.input(
                    placeholder=self.placeholder,
                    value=self.value,
                    on_change=self._handle_change
                ).classes('rag-input w-full')
            
            # 無効化
            if self.disabled:
                input_element.props('disabled')
            
            # エラーメッセージ
            if self.error_message:
                ui.label(self.error_message).classes('text-red-600 text-sm mt-1')
            
            return input_element
    
    def _handle_change(self, e):
        """変更ハンドラー"""
        # バリデーション実行
        if self.validation:
            try:
                self.validation(e.value)
                self.error_message = ""
            except ValueError as error:
                self.error_message = str(error)
        
        # 変更コールバック実行
        if self.on_change:
            self.on_change(e)
    
    def get_value(self):
        """値取得"""
        return self.input_element.value
    
    def set_value(self, value):
        """値設定"""
        self.input_element.value = value
    
    def set_error(self, message: str):
        """エラー設定"""
        self.error_message = message

class RAGSelect:
    """統一セレクトボックスコンポーネント"""
    
    def __init__(
        self,
        label: str,
        options: List[Dict[str, Any]],
        value: Any = None,
        required: bool = False,
        on_change: Optional[Callable] = None,
        disabled: bool = False,
        clearable: bool = False
    ):
        self.label = label
        self.options = options
        self.value = value
        self.required = required
        self.on_change = on_change
        self.disabled = disabled
        self.clearable = clearable
        
        self.select_element = self._create_select()
    
    def _create_select(self):
        """セレクトボックス作成"""
        with ui.column().classes('w-full mb-4'):
            # ラベル
            label_classes = 'block text-sm font-medium text-gray-700 mb-1'
            if self.required:
                ui.label(f'{self.label} *').classes(label_classes + ' text-red-600')
            else:
                ui.label(self.label).classes(label_classes)
            
            # セレクトボックス
            select_element = ui.select(
                options=self.options,
                value=self.value,
                on_change=self.on_change,
                clearable=self.clearable
            ).classes('rag-input w-full')
            
            if self.disabled:
                select_element.props('disabled')
            
            return select_element
    
    def get_value(self):
        """値取得"""
        return self.select_element.value
    
    def set_value(self, value):
        """値設定"""
        self.select_element.value = value

class RAGTextArea:
    """統一テキストエリアコンポーネント"""
    
    def __init__(
        self,
        label: str,
        placeholder: str = "",
        value: str = "",
        rows: int = 4,
        required: bool = False,
        on_change: Optional[Callable] = None,
        disabled: bool = False
    ):
        self.label = label
        self.placeholder = placeholder
        self.value = value
        self.rows = rows
        self.required = required
        self.on_change = on_change
        self.disabled = disabled
        
        self.textarea_element = self._create_textarea()
    
    def _create_textarea(self):
        """テキストエリア作成"""
        with ui.column().classes('w-full mb-4'):
            # ラベル
            label_classes = 'block text-sm font-medium text-gray-700 mb-1'
            if self.required:
                ui.label(f'{self.label} *').classes(label_classes + ' text-red-600')
            else:
                ui.label(self.label).classes(label_classes)
            
            # テキストエリア
            textarea_element = ui.textarea(
                placeholder=self.placeholder,
                value=self.value,
                on_change=self.on_change
            ).classes('rag-input w-full').props(f'rows={self.rows}')
            
            if self.disabled:
                textarea_element.props('disabled')
            
            return textarea_element
    
    def get_value(self):
        """値取得"""
        return self.textarea_element.value
    
    def set_value(self, value):
        """値設定"""
        self.textarea_element.value = value

class RAGButton:
    """統一ボタンコンポーネント"""
    
    def __init__(
        self,
        label: str,
        on_click: Optional[Callable] = None,
        button_type: str = "primary",  # primary, secondary, outline, danger
        size: str = "medium",  # small, medium, large
        disabled: bool = False,
        loading: bool = False,
        icon: Optional[str] = None,
        full_width: bool = False
    ):
        self.label = label
        self.on_click = on_click
        self.button_type = button_type
        self.size = size
        self.disabled = disabled
        self.loading = loading
        self.icon = icon
        self.full_width = full_width
        
        self.button_element = self._create_button()
    
    def _create_button(self):
        """ボタン作成"""
        # ベースクラス
        classes = 'rag-button transition-all duration-200'
        
        # タイプ別スタイル
        if self.button_type == "secondary":
            classes += ' rag-button-secondary'
        elif self.button_type == "outline":
            classes += ' rag-button-outline'
        elif self.button_type == "danger":
            classes += ' bg-red-600 hover:bg-red-700 text-white'
        
        # サイズ
        if self.size == "small":
            classes += ' px-3 py-1 text-sm'
        elif self.size == "large":
            classes += ' px-8 py-4 text-lg'
        
        # 幅
        if self.full_width:
            classes += ' w-full'
        
        # ボタン作成
        button_text = f"{self.icon} {self.label}" if self.icon else self.label
        
        button_element = ui.button(
            button_text,
            on_click=self.on_click
        ).classes(classes)
        
        if self.disabled:
            button_element.props('disabled')
        
        if self.loading:
            button_element.props('loading')
        
        return button_element
    
    def set_loading(self, loading: bool):
        """ローディング状態設定"""
        self.loading = loading
        if loading:
            self.button_element.props('loading')
        else:
            self.button_element.props('remove=loading')

class RAGFileUpload:
    """統一ファイルアップロードコンポーネント"""
    
    def __init__(
        self,
        label: str,
        accept: Optional[str] = None,
        multiple: bool = False,
        max_size: Optional[int] = None,
        on_upload: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ):
        self.label = label
        self.accept = accept
        self.multiple = multiple
        self.max_size = max_size
        self.on_upload = on_upload
        self.on_error = on_error
        
        self.upload_element = self._create_upload()
    
    def _create_upload(self):
        """ファイルアップロード作成"""
        with ui.column().classes('w-full mb-4'):
            # ラベル
            ui.label(self.label).classes('block text-sm font-medium text-gray-700 mb-1')
            
            # アップロードエリア
            upload_element = ui.upload(
                on_upload=self._handle_upload,
                multiple=self.multiple,
                auto_upload=True
            ).classes('w-full')
            
            if self.accept:
                upload_element.props(f'accept="{self.accept}"')
            
            # アップロード説明
            accept_text = self.accept or "すべてのファイル"
            size_text = f"最大 {self.max_size // (1024*1024)}MB" if self.max_size else ""
            ui.label(f'対応形式: {accept_text} {size_text}').classes('text-sm text-gray-500 mt-1')
            
            return upload_element
    
    def _handle_upload(self, e):
        """アップロードハンドラー"""
        try:
            # サイズチェック
            if self.max_size and e.size > self.max_size:
                if self.on_error:
                    self.on_error(f"ファイルサイズが上限を超えています: {e.size} bytes")
                return
            
            # アップロードコールバック実行
            if self.on_upload:
                self.on_upload(e)
                
        except Exception as error:
            if self.on_error:
                self.on_error(str(error))

class RAGForm:
    """統一フォームコンポーネント"""
    
    def __init__(
        self,
        title: str = "",
        submit_label: str = "送信",
        cancel_label: str = "キャンセル",
        on_submit: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        show_cancel: bool = True
    ):
        self.title = title
        self.submit_label = submit_label
        self.cancel_label = cancel_label
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.show_cancel = show_cancel
        
        self.fields = []
        self.form_container = self._create_form()
    
    def _create_form(self):
        """フォーム作成"""
        with ui.card().classes('rag-card p-6'):
            if self.title:
                ui.label(self.title).classes('text-xl font-bold mb-4')
            
            # フィールドコンテナ
            fields_container = ui.column().classes('w-full')
            
            # ボタンエリア
            with ui.row().classes('w-full justify-end gap-4 mt-6'):
                if self.show_cancel:
                    RAGButton(
                        self.cancel_label,
                        on_click=self.on_cancel,
                        button_type="outline"
                    )
                
                RAGButton(
                    self.submit_label,
                    on_click=self._handle_submit,
                    button_type="primary"
                )
            
            return fields_container
    
    def add_field(self, field_component):
        """フィールド追加"""
        self.fields.append(field_component)
        with self.form_container:
            field_component
    
    def _handle_submit(self):
        """送信ハンドラー"""
        # バリデーション実行
        is_valid = True
        form_data = {}
        
        for field in self.fields:
            if hasattr(field, 'get_value'):
                field_value = field.get_value()
                form_data[field.label] = field_value
                
                # 必須チェック
                if hasattr(field, 'required') and field.required and not field_value:
                    field.set_error(f'{field.label}は必須です')
                    is_valid = False
        
        # 送信処理
        if is_valid and self.on_submit:
            self.on_submit(form_data)
    
    def get_form_data(self) -> Dict[str, Any]:
        """フォームデータ取得"""
        form_data = {}
        for field in self.fields:
            if hasattr(field, 'get_value'):
                form_data[field.label] = field.get_value()
        return form_data