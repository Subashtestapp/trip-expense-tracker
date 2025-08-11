"""
Trip Expense Tracker - Android App
Built with Kivy for cross-platform compatibility
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from datetime import datetime
import json
import os
from kivy.utils import platform

class TripData:
    """Data management class for trip expenses"""
    
    def __init__(self):
        self.reset_trip()
        self.data_file = self.get_data_path()
        self.load_data()
    
    def get_data_path(self):
        """Get appropriate data storage path based on platform"""
        if platform == 'android':
            from android.storage import primary_external_storage_path
            return os.path.join(primary_external_storage_path(), 'trip_expenses.json')
        else:
            return 'trip_expenses.json'
    
    def reset_trip(self):
        self.trip_name = ""
        self.participants = []
        self.expenses = []
    
    def add_participant(self, name):
        if name and name not in self.participants:
            self.participants.append(name)
            return True
        return False
    
    def remove_participant(self, name):
        if name in self.participants:
            self.participants.remove(name)
            # Remove this participant from all expenses
            for expense in self.expenses:
                if name in expense['paid_by']:
                    expense['paid_by'].remove(name)
                if name in expense['split_among']:
                    expense['split_among'].remove(name)
            return True
        return False
    
    def add_expense(self, description, amount, paid_by, split_among, category="General"):
        expense = {
            'id': len(self.expenses) + 1,
            'description': description,
            'amount': float(amount),
            'paid_by': paid_by,
            'split_among': split_among,
            'category': category,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.expenses.append(expense)
        self.save_data()
        return expense
    
    def remove_expense(self, expense_id):
        self.expenses = [e for e in self.expenses if e['id'] != expense_id]
        self.save_data()
    
    def calculate_balances(self):
        """Calculate who owes whom how much"""
        balances = {person: 0.0 for person in self.participants}
        
        for expense in self.expenses:
            amount_per_person = expense['amount'] / len(expense['split_among'])
            
            # Add to paid_by balance
            for payer in expense['paid_by']:
                balances[payer] += expense['amount'] / len(expense['paid_by'])
            
            # Subtract from split_among balance
            for person in expense['split_among']:
                balances[person] -= amount_per_person
        
        return balances
    
    def get_settlements(self):
        """Calculate optimal settlement transactions"""
        balances = self.calculate_balances()
        
        creditors = [(person, amount) for person, amount in balances.items() if amount > 0.01]
        debtors = [(person, -amount) for person, amount in balances.items() if amount < -0.01]
        
        settlements = []
        
        for debtor_name, debt_amount in debtors:
            remaining_debt = debt_amount
            
            for i, (creditor_name, credit_amount) in enumerate(creditors):
                if remaining_debt <= 0.01:
                    break
                
                settlement_amount = min(remaining_debt, credit_amount)
                if settlement_amount > 0.01:
                    settlements.append({
                        'from': debtor_name,
                        'to': creditor_name,
                        'amount': round(settlement_amount, 2)
                    })
                    
                    creditors[i] = (creditor_name, credit_amount - settlement_amount)
                    remaining_debt -= settlement_amount
        
        return settlements
    
    def get_summary(self):
        """Get trip summary statistics"""
        total_expenses = sum(expense['amount'] for expense in self.expenses)
        cost_per_person = total_expenses / len(self.participants) if self.participants else 0
        
        category_totals = {}
        for expense in self.expenses:
            category = expense['category']
            category_totals[category] = category_totals.get(category, 0) + expense['amount']
        
        return {
            'total_expenses': total_expenses,
            'cost_per_person': cost_per_person,
            'num_expenses': len(self.expenses),
            'category_totals': category_totals
        }
    
    def save_data(self):
        """Save trip data to file"""
        data = {
            'trip_name': self.trip_name,
            'participants': self.participants,
            'expenses': self.expenses
        }
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def load_data(self):
        """Load trip data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.trip_name = data.get('trip_name', '')
                    self.participants = data.get('participants', [])
                    self.expenses = data.get('expenses', [])
        except Exception as e:
            print(f"Error loading data: {e}")

class MainScreen(Screen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(text='Trip Expense Tracker', font_size=24, size_hint_y=None, height=50)
        layout.add_widget(title)
        
        # Trip name input
        trip_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        trip_layout.add_widget(Label(text='Trip Name:', size_hint_x=0.3))
        self.trip_input = TextInput(multiline=False)
        self.trip_input.bind(text=self.on_trip_name_change)
        trip_layout.add_widget(self.trip_input)
        layout.add_widget(trip_layout)
        
        # Participants section
        participants_label = Label(text='Participants', font_size=18, size_hint_y=None, height=40)
        layout.add_widget(participants_label)
        
        # Add participant
        add_participant_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.participant_input = TextInput(hint_text='Enter participant name', multiline=False)
        add_participant_btn = Button(text='Add Participant', size_hint_x=0.3)
        add_participant_btn.bind(on_press=self.add_participant)
        add_participant_layout.add_widget(self.participant_input)
        add_participant_layout.add_widget(add_participant_btn)
        layout.add_widget(add_participant_layout)
        
        # Participants list
        self.participants_layout = GridLayout(cols=2, size_hint_y=None)
        self.participants_layout.bind(minimum_height=self.participants_layout.setter('height'))
        participants_scroll = ScrollView(size_hint_y=0.3)
        participants_scroll.add_widget(self.participants_layout)
        layout.add_widget(participants_scroll)
        
        # Navigation buttons
        nav_layout = GridLayout(cols=2, size_hint_y=None, height=100, spacing=10)
        
        add_expense_btn = Button(text='Add Expense')
        add_expense_btn.bind(on_press=lambda x: self.app.go_to_screen('add_expense'))
        
        view_summary_btn = Button(text='View Summary')
        view_summary_btn.bind(on_press=lambda x: self.app.go_to_screen('summary'))
        
        nav_layout.add_widget(add_expense_btn)
        nav_layout.add_widget(view_summary_btn)
        layout.add_widget(nav_layout)
        
        self.add_widget(layout)
        self.refresh_participants()
    
    def on_trip_name_change(self, instance, value):
        self.app.trip_data.trip_name = value
        self.app.trip_data.save_data()
    
    def add_participant(self, instance):
        name = self.participant_input.text.strip()
        if self.app.trip_data.add_participant(name):
            self.participant_input.text = ''
            self.refresh_participants()
            self.app.trip_data.save_data()
        else:
            self.show_popup('Error', 'Participant already exists or name is empty')
    
    def remove_participant(self, name):
        self.app.trip_data.remove_participant(name)
        self.refresh_participants()
        self.app.trip_data.save_data()
    
    def refresh_participants(self):
        self.participants_layout.clear_widgets()
        for participant in self.app.trip_data.participants:
            self.participants_layout.add_widget(Label(text=participant))
            remove_btn = Button(text='Remove', size_hint_x=0.3)
            remove_btn.bind(on_press=lambda x, name=participant: self.remove_participant(name))
            self.participants_layout.add_widget(remove_btn)
        
        # Update trip name display
        self.trip_input.text = self.app.trip_data.trip_name
    
    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()

class AddExpenseScreen(Screen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(text='Add New Expense', font_size=24, size_hint_y=None, height=50)
        layout.add_widget(title)
        
        # Form fields
        form_layout = GridLayout(cols=2, size_hint_y=None, spacing=10)
        form_layout.bind(minimum_height=form_layout.setter('height'))
        
        # Description
        form_layout.add_widget(Label(text='Description:', size_hint_y=None, height=40))
        self.description_input = TextInput(multiline=False, size_hint_y=None, height=40)
        form_layout.add_widget(self.description_input)
        
        # Amount
        form_layout.add_widget(Label(text='Amount:', size_hint_y=None, height=40))
        self.amount_input = TextInput(input_filter='float', multiline=False, size_hint_y=None, height=40)
        form_layout.add_widget(self.amount_input)
        
        # Category
        form_layout.add_widget(Label(text='Category:', size_hint_y=None, height=40))
        self.category_spinner = Spinner(
            text='General',
            values=['General', 'Food', 'Transportation', 'Accommodation', 'Entertainment', 'Shopping', 'Other'],
            size_hint_y=None,
            height=40
        )
        form_layout.add_widget(self.category_spinner)
        
        layout.add_widget(form_layout)
        
        # Paid by section
        paid_by_label = Label(text='Paid by:', font_size=16, size_hint_y=None, height=30)
        layout.add_widget(paid_by_label)
        
        self.paid_by_layout = GridLayout(cols=3, size_hint_y=None)
        self.paid_by_layout.bind(minimum_height=self.paid_by_layout.setter('height'))
        paid_by_scroll = ScrollView(size_hint_y=0.2)
        paid_by_scroll.add_widget(self.paid_by_layout)
        layout.add_widget(paid_by_scroll)
        
        # Split among section
        split_among_label = Label(text='Split among:', font_size=16, size_hint_y=None, height=30)
        layout.add_widget(split_among_label)
        
        self.split_among_layout = GridLayout(cols=3, size_hint_y=None)
        self.split_among_layout.bind(minimum_height=self.split_among_layout.setter('height'))
        split_among_scroll = ScrollView(size_hint_y=0.2)
        split_among_scroll.add_widget(self.split_among_layout)
        layout.add_widget(split_among_scroll)
        
        # Buttons
        btn_layout = GridLayout(cols=2, size_hint_y=None, height=50, spacing=10)
        
        save_btn = Button(text='Save Expense')
        save_btn.bind(on_press=self.save_expense)
        
        back_btn = Button(text='Back')
        back_btn.bind(on_press=lambda x: self.app.go_to_screen('main'))
        
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(back_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
        
        # Initialize checkboxes
        self.paid_by_checkboxes = {}
        self.split_among_checkboxes = {}
    
    def on_pre_enter(self):
        """Called when screen is about to be displayed"""
        self.refresh_participants()
    
    def refresh_participants(self):
        """Refresh the participant checkboxes"""
        self.paid_by_layout.clear_widgets()
        self.split_among_layout.clear_widgets()
        self.paid_by_checkboxes.clear()
        self.split_among_checkboxes.clear()
        
        for participant in self.app.trip_data.participants:
            # Paid by checkboxes
            paid_by_btn = Button(text=f'☐ {participant}', size_hint_y=None, height=30)
            paid_by_btn.participant = participant
            paid_by_btn.selected = False
            paid_by_btn.bind(on_press=self.toggle_paid_by)
            self.paid_by_layout.add_widget(paid_by_btn)
            self.paid_by_checkboxes[participant] = paid_by_btn
            
            # Split among checkboxes
            split_among_btn = Button(text=f'☐ {participant}', size_hint_y=None, height=30)
            split_among_btn.participant = participant
            split_among_btn.selected = False
            split_among_btn.bind(on_press=self.toggle_split_among)
            self.split_among_layout.add_widget(split_among_btn)
            self.split_among_checkboxes[participant] = split_among_btn
    
    def toggle_paid_by(self, instance):
        instance.selected = not instance.selected
        if instance.selected:
            instance.text = f'☑ {instance.participant}'
        else:
            instance.text = f'☐ {instance.participant}'
    
    def toggle_split_among(self, instance):
        instance.selected = not instance.selected
        if instance.selected:
            instance.text = f'☑ {instance.participant}'
        else:
            instance.text = f'☐ {instance.participant}'
    
    def save_expense(self, instance):
        description = self.description_input.text.strip()
        amount = self.amount_input.text.strip()
        
        if not description or not amount:
            self.show_popup('Error', 'Please fill in description and amount')
            return
        
        try:
            amount = float(amount)
        except ValueError:
            self.show_popup('Error', 'Please enter a valid amount')
            return
        
        paid_by = [p for p, btn in self.paid_by_checkboxes.items() if btn.selected]
        split_among = [p for p, btn in self.split_among_checkboxes.items() if btn.selected]
        
        if not paid_by:
            self.show_popup('Error', 'Please select who paid for this expense')
            return
        
        if not split_among:
            self.show_popup('Error', 'Please select who to split this expense among')
            return
        
        self.app.trip_data.add_expense(
            description, amount, paid_by, split_among, self.category_spinner.text
        )
        
        # Clear form
        self.description_input.text = ''
        self.amount_input.text = ''
        self.category_spinner.text = 'General'
        
        # Uncheck all checkboxes
        for btn in self.paid_by_checkboxes.values():
            btn.selected = False
            btn.text = f'☐ {btn.participant}'
        
        for btn in self.split_among_checkboxes.values():
            btn.selected = False
            btn.text = f'☐ {btn.participant}'
        
        self.show_popup('Success', 'Expense added successfully!')
    
    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()

class SummaryScreen(Screen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(text='Trip Summary', font_size=24, size_hint_y=None, height=50)
        layout.add_widget(title)
        
        # Summary content
        self.summary_layout = BoxLayout(orientation='vertical')
        summary_scroll = ScrollView()
        summary_scroll.add_widget(self.summary_layout)
        layout.add_widget(summary_scroll)
        
        # Buttons
        btn_layout = GridLayout(cols=3, size_hint_y=None, height=50, spacing=10)
        
        share_btn = Button(text='Share Summary')
        share_btn.bind(on_press=self.share_summary)
        
        expenses_btn = Button(text='View Expenses')
        expenses_btn.bind(on_press=lambda x: self.app.go_to_screen('expenses'))
        
        back_btn = Button(text='Back')
        back_btn.bind(on_press=lambda x: self.app.go_to_screen('main'))
        
        btn_layout.add_widget(share_btn)
        btn_layout.add_widget(expenses_btn)
        btn_layout.add_widget(back_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def on_pre_enter(self):
        """Called when screen is about to be displayed"""
        self.refresh_summary()
    
    def refresh_summary(self):
        self.summary_layout.clear_widgets()
        
        if not self.app.trip_data.participants:
            self.summary_layout.add_widget(Label(text='No participants added yet.'))
            return
        
        if not self.app.trip_data.expenses:
            self.summary_layout.add_widget(Label(text='No expenses added yet.'))
            return
        
        summary = self.app.trip_data.get_summary()
        settlements = self.app.trip_data.get_settlements()
        
        # Trip overview
        trip_name = self.app.trip_data.trip_name or "Untitled Trip"
        self.summary_layout.add_widget(Label(text=f'Trip: {trip_name}', font_size=18, size_hint_y=None, height=30))
        self.summary_layout.add_widget(Label(text=f'Total Expenses: ${summary["total_expenses"]:.2f}', size_hint_y=None, height=30))
        self.summary_layout.add_widget(Label(text=f'Cost per Person: ${summary["cost_per_person"]:.2f}', size_hint_y=None, height=30))
        self.summary_layout.add_widget(Label(text=f'Number of Expenses: {summary["num_expenses"]}', size_hint_y=None, height=30))
        
        # Category breakdown
        if summary["category_totals"]:
            self.summary_layout.add_widget(Label(text='\nCategory Breakdown:', font_size=16, size_hint_y=None, height=40))
            for category, total in summary["category_totals"].items():
                self.summary_layout.add_widget(Label(text=f'{category}: ${total:.2f}', size_hint_y=None, height=25))
        
        # Settlements
        if settlements:
            self.summary_layout.add_widget(Label(text='\nWho Owes Whom:', font_size=16, size_hint_y=None, height=40))
            for settlement in settlements:
                settlement_text = f'{settlement["from"]} owes {settlement["to"]}: ${settlement["amount"]:.2f}'
                self.summary_layout.add_widget(Label(text=settlement_text, size_hint_y=None, height=25))
        else:
            self.summary_layout.add_widget(Label(text='\nAll expenses are settled!', font_size=16, size_hint_y=None, height=40))
    
    def share_summary(self, instance):
        """Generate shareable summary text"""
        if not self.app.trip_data.participants or not self.app.trip_data.expenses:
            self.show_popup('Error', 'No data to share')
            return
        
        summary = self.app.trip_data.get_summary()
        settlements = self.app.trip_data.get_settlements()
        trip_name = self.app.trip_data.trip_name or "Untitled Trip"
        
        share_text = f"💰 {trip_name} - Expense Summary\n\n"
        share_text += f"📊 Total Expenses: ${summary['total_expenses']:.2f}\n"
        share_text += f"👥 Cost per Person: ${summary['cost_per_person']:.2f}\n"
        share_text += f"🧾 Number of Expenses: {summary['num_expenses']}\n\n"
        
        if summary["category_totals"]:
            share_text += "📈 Category Breakdown:\n"
            for category, total in summary["category_totals"].items():
                share_text += f"• {category}: ${total:.2f}\n"
            share_text += "\n"
        
        if settlements:
            share_text += "💳 Settlement Details:\n"
            for settlement in settlements:
                share_text += f"• {settlement['from']} owes {settlement['to']}: ${settlement['amount']:.2f}\n"
        else:
            share_text += "✅ All expenses are settled!\n"
        
        share_text += f"\nGenerated by Trip Expense Tracker 📱"
        
        # On Android, use the sharing intent
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                String = autoclass('java.lang.String')
                
                intent = Intent()
                intent.setAction(Intent.ACTION_SEND)
                intent.putExtra(Intent.EXTRA_TEXT, String(share_text))
                intent.setType('text/plain')
                
                chooser = Intent.createChooser(intent, String('Share Trip Summary'))
                PythonActivity.mActivity.startActivity(chooser)
            except Exception as e:
                print(f"Error sharing: {e}")
                self.show_text_popup('Share Summary', share_text)
        else:
            # For desktop, show in popup
            self.show_text_popup('Share Summary', share_text)
    
    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()
    
    def show_text_popup(self, title, text):
        content = BoxLayout(orientation='vertical')
        text_input = TextInput(text=text, readonly=True, multiline=True)
        close_btn = Button(text='Close', size_hint_y=None, height=40)
        content.add_widget(text_input)
        content.add_widget(close_btn)
        
        popup = Popup(title=title, content=content, size_hint=(0.9, 0.8))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

class ExpensesScreen(Screen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(text='All Expenses', font_size=24, size_hint_y=None, height=50)
        layout.add_widget(title)
        
        # Expenses list
        self.expenses_layout = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.expenses_layout.bind(minimum_height=self.expenses_layout.setter('height'))
        expenses_scroll = ScrollView()
        expenses_scroll.add_widget(self.expenses_layout)
        layout.add_widget(expenses_scroll)
        
        # Back button
        back_btn = Button(text='Back', size_hint_y=None, height=50)
        back_btn.bind(on_press=lambda x: self.app.go_to_screen('summary'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def on_pre_enter(self):
        """Called when screen is about to be displayed"""
        self.refresh_expenses()
    
    def refresh_expenses(self):
        self.expenses_layout.clear_widgets()
        
        if not self.app.trip_data.expenses:
            self.expenses_layout.add_widget(Label(text='No expenses added yet.', size_hint_y=None, height=40))
            return
        
        for expense in reversed(self.app.trip_data.expenses):  # Show newest first
            expense_widget = self.create_expense_widget(expense)
            self.expenses_layout.add_widget(expense_widget)
    
    def create_expense_widget(self, expense):
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=100, padding=5)
        layout.canvas.before.clear()
        
        # Main expense info
        main_layout = BoxLayout(orientation='horizontal')
        
        info_layout = BoxLayout(orientation='vertical')
        info_layout.add_widget(Label(text=f"{expense['description']} - ${expense['amount']:.2f}", font_size=16, halign='left'))
        info_layout.add_widget(Label(text=f"Category: {expense['category']} | Date: {expense['date']}", font_size=12, halign='left'))
        info_layout.add_widget(Label(text=f"Paid by: {', '.join(expense['paid_by'])} | Split among: {', '.join(expense['split_among'])}", font_size=12, halign='left'))
        
        main_layout.add_widget(info_layout)
        
        # Delete button
        delete_btn = Button(text='Delete', size_hint_x=None, width=80)
        delete_btn.bind(on_press=lambda x, eid=expense['id']: self.delete_expense(eid))
        main_layout.add_widget(delete_btn)
        
        layout.add_widget(main_layout)
        
        return layout
    
    def delete_expense(self, expense_id):
        self.app.trip_data.remove_expense(expense_id)
        self.refresh_expenses()

class TripExpenseApp(App):
    def build(self):
        self.trip_data = TripData()
        
        # Create screen manager
        self.sm = ScreenManager()
        
        # Create screens
        self.main_screen = MainScreen(self, name='main')
        self.add_expense_screen = AddExpenseScreen(self, name='add_expense')
        self.summary_screen = SummaryScreen(self, name='summary')
        self.expenses_screen = ExpensesScreen(self, name='expenses')
        
        # Add screens to manager
        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.add_expense_screen)
        self.sm.add_widget(self.summary_screen)
        self.sm.add_widget(self.expenses_screen)
        
        return self.sm
    
    def go_to_screen(self, screen_name):
        self.sm.current = screen_name
    
    def on_pause(self):
        """Handle app pause (Android lifecycle)"""
        return True
    
    def on_resume(self):
        """Handle app resume (Android lifecycle)"""
        pass

if __name__ == '__main__':
    TripExpenseApp().