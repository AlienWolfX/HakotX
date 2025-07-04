import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
import csv

# Color scheme
COLORS = {
    'primary': get_color_from_hex('#6200EE'),
    'primary_variant': get_color_from_hex('#3700B3'),
    'secondary': get_color_from_hex('#03DAC6'),
    'background': get_color_from_hex('#FFFFFF'),
    'surface': get_color_from_hex('#FFFFFF'),
    'error': get_color_from_hex('#B00020'),
    'on_primary': get_color_from_hex('#FFFFFF'),
    'on_secondary': get_color_from_hex('#000000'),
    'on_background': get_color_from_hex('#000000'),
    'on_surface': get_color_from_hex('#000000'),
    'on_error': get_color_from_hex('#FFFFFF')
}

class MaterialButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.color = COLORS['on_primary']
        self.font_size = dp(14)
        self.bold = True
        self.size_hint_y = None
        self.height = dp(48)
        
        with self.canvas.before:
            Color(*COLORS['primary'])
            self.rect = RoundedRectangle(
                size=self.size,
                pos=self.pos,
                radius=[dp(4),]
            )
        
        self.bind(pos=self.update_rect, size=self.update_rect)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def on_press(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['primary_variant'])
            self.rect = RoundedRectangle(
                size=self.size,
                pos=self.pos,
                radius=[dp(4),]
            )
        Clock.schedule_once(self.reset_color, 0.1)
    
    def reset_color(self, dt):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['primary'])
            self.rect = RoundedRectangle(
                size=self.size,
                pos=self.pos,
                radius=[dp(4),]
            )

class MaterialTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0, 0, 0, 0)
        self.multiline = False
        self.padding = [dp(12), dp(12), dp(12), dp(12)]
        self.font_size = dp(16)
        self.hint_text_color = get_color_from_hex('#808080')
        self.size_hint_y = None
        self.height = dp(48)
        
        with self.canvas.before:
            Color(*COLORS['on_surface'])
            self.underline = Rectangle(
                pos=(self.x, self.y),
                size=(self.width, dp(1))
            )
        
        self.bind(pos=self.update_underline, size=self.update_underline)
    
    def update_underline(self, *args):
        self.underline.pos = (self.x, self.y)
        self.underline.size = (self.width, dp(1))
    
    def on_focus(self, instance, value):
        if value:
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*COLORS['primary'])
                self.underline = Rectangle(
                    pos=(self.x, self.y),
                    size=(self.width, dp(2))
                )
        else:
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*COLORS['on_surface'])
                self.underline = Rectangle(
                    pos=(self.x, self.y),
                    size=(self.width, dp(1))
                )

class ResultCard(BoxLayout):
    filename = StringProperty('')
    row_number = StringProperty('')
    content = StringProperty('')
    file_path = StringProperty('')
    columns = StringProperty('')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(120)  # Increased height to accommodate columns
        self.padding = dp(12)
        self.spacing = dp(8)
        
        with self.canvas.before:
            Color(*COLORS['surface'])
            self.rect = RoundedRectangle(
                size=self.size,
                pos=self.pos,
                radius=[dp(8),]
            )
            Color(*get_color_from_hex('#E0E0E0'))
            self.border = RoundedRectangle(
                size=self.size,
                pos=self.pos,
                radius=[dp(8),]
            )
        
        self.bind(pos=self.update_rect, size=self.update_rect)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.pos = (self.pos[0]-dp(1), self.pos[1]-dp(1))
        self.border.size = (self.size[0]+dp(2), self.size[1]+dp(2))
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*get_color_from_hex('#F5F5F5'))
                self.rect = RoundedRectangle(
                    size=self.size,
                    pos=self.pos,
                    radius=[dp(8),]
                )
                Color(*get_color_from_hex('#E0E0E0'))
                self.border = RoundedRectangle(
                    size=self.size,
                    pos=self.pos,
                    radius=[dp(8),]
                )
            return True
        return super().on_touch_down(touch)
    
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*COLORS['surface'])
                self.rect = RoundedRectangle(
                    size=self.size,
                    pos=self.pos,
                    radius=[dp(8),]
                )
                Color(*get_color_from_hex('#E0E0E0'))
                self.border = RoundedRectangle(
                    size=self.size,
                    pos=self.pos,
                    radius=[dp(8),]
                )
            if self.collide_point(*touch.pos):
                # Handle card click here if needed
                pass
            return True
        return super().on_touch_up(touch)

class SearchApp(App):
    search_active = BooleanProperty(False)
    result_count = NumericProperty(0)
    
    def build(self):
        # Set window properties
        Window.size = (dp(1000), dp(700))
        Window.minimum_width = dp(800)
        Window.minimum_height = dp(600)
        self.title = 'HakotX Search'
        Window.clearcolor = COLORS['background']
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(16))
        
        # Header
        header = BoxLayout(size_hint_y=None, height=dp(72))
        title = Label(
            text='Credentials Lookup',
            font_size='24sp',
            bold=True,
            color=COLORS['on_background'],
            halign='left',
            valign='center'
        )
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)
        
        # Add a spacer
        header.add_widget(Label(size_hint_x=None, width=dp(16)))
        
        # Search stats
        self.stats_label = Label(
            text=f'Results: {self.result_count}',
            font_size='14sp',
            color=COLORS['on_background'],
            halign='right',
            valign='center',
            size_hint_x=None,
            width=dp(120)
        )
        self.stats_label.bind(size=self.stats_label.setter('text_size'))
        header.add_widget(self.stats_label)
        
        main_layout.add_widget(header)
        
        # Search bar
        search_bar = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(16))
        self.search_input = MaterialTextInput(
            hint_text='Search across CSV files...',
            size_hint_x=0.8
        )
        self.search_input.bind(on_text_validate=self.search_files)
        
        self.search_button = MaterialButton(
            text='SEARCH',
            size_hint_x=0.2
        )
        self.search_button.bind(on_press=self.search_files)
        
        search_bar.add_widget(self.search_input)
        search_bar.add_widget(self.search_button)
        main_layout.add_widget(search_bar)
        
        # Results area
        results_container = BoxLayout()
        
        self.scroll_view = ScrollView(do_scroll_x=False)
        self.results_layout = GridLayout(
            cols=1,
            spacing=dp(12),
            size_hint_y=None,
            padding=[dp(8), dp(8), dp(8), dp(8)]
        )
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        
        self.scroll_view.add_widget(self.results_layout)
        results_container.add_widget(self.scroll_view)
        main_layout.add_widget(results_container)
        
        # Add initial placeholder
        self.show_placeholder("Enter a search term to begin")
        
        return main_layout
    
    def show_placeholder(self, message):
        self.results_layout.clear_widgets()
        placeholder = Label(
            text=message,
            font_size='16sp',
            color=COLORS['on_background'],
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(200)
        )
        placeholder.bind(size=placeholder.setter('text_size'))
        self.results_layout.add_widget(placeholder)
    
    def search_files(self, instance):
        search_term = self.search_input.text.strip().lower()
        self.results_layout.clear_widgets()
        self.result_count = 0
        
        if not search_term:
            self.show_placeholder("Please enter a search term")
            return
        
        # Show loading indicator
        loading = Label(
            text="Searching...",
            font_size='16sp',
            color=COLORS['on_background'],
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(200)
        )
        loading.bind(size=loading.setter('text_size'))
        self.results_layout.add_widget(loading)
        
        # Process search in the next frame to allow UI to update
        Clock.schedule_once(lambda dt: self._perform_search(search_term), 0.1)
    
    def _perform_search(self, search_term):
        self.results_layout.clear_widgets()
        csv_folder = os.path.join(os.path.dirname(__file__), 'csv')
        
        if not os.path.exists(csv_folder):
            self.show_placeholder("CSV folder not found!")
            return
        
        found_results = False
        
        for root, dirs, files in os.walk(csv_folder):
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as csvfile:
                            reader = csv.reader(csvfile)
                            headers = next(reader)  # Get column headers
                            
                            for row_num, row in enumerate(reader, 1):
                                if any(search_term in str(cell).lower() for cell in row):
                                    found_results = True
                                    self.result_count += 1
                                    
                                    # Create a result card
                                    card = ResultCard()
                                    card.filename = file
                                    card.row_number = f"Row {row_num}"
                                    card.file_path = file_path
                                    
                                    # Add filename label
                                    filename_label = Label(
                                        text=f"[b]{file}[/b]",
                                        font_size='14sp',
                                        color=COLORS['primary'],
                                        halign='left',
                                        size_hint_y=None,
                                        height=dp(24),
                                        markup=True
                                    )
                                    filename_label.bind(size=filename_label.setter('text_size'))
                                    card.add_widget(filename_label)
                                    
                                    # Add row number label
                                    row_label = Label(
                                        text=f"[i]Row {row_num}[/i]",
                                        font_size='12sp',
                                        color=COLORS['on_surface'],
                                        halign='left',
                                        size_hint_y=None,
                                        height=dp(20),
                                        markup=True
                                    )
                                    row_label.bind(size=row_label.setter('text_size'))
                                    card.add_widget(row_label)
                                    
                                    # Add column headers and values
                                    column_values = []
                                    for header, value in zip(headers, row):
                                        column_values.append(f"[b]{header}:[/b] {value}")
                                    
                                    # Add content label with columns
                                    content_label = Label(
                                        text="\n".join(column_values),
                                        font_size='14sp',
                                        color=COLORS['on_background'],
                                        halign='left',
                                        size_hint_y=None,
                                        height=dp(60),  # Increased height for multiple lines
                                        text_size=(self.scroll_view.width - dp(48), None),
                                        markup=True
                                    )
                                    content_label.bind(size=content_label.setter('text_size'))
                                    card.add_widget(content_label)
                                    
                                    self.results_layout.add_widget(card)
                    except Exception as e:
                        print(f"Error reading {file}: {str(e)}")
        
        # Update stats
        self.stats_label.text = f'Results: {self.result_count}'
        
        if not found_results:
            self.show_placeholder("No results found for your search")

if __name__ == '__main__':
    SearchApp().run()