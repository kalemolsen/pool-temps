import tkinter
import tkinter.messagebox
from tkinter import ttk
import customtkinter
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter
import os
import pytz




customtkinter.set_ctk_parent_class(tkinter.Tk)

customtkinter.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class DatabaseManager:
    def __init__(self, db_path) -> None:
        self.db_path = db_path
        self.create_database()

    def create_database(self):
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS temperatures (
                    id INTEGER PRIMARY KEY,
                    pool_name TEXT,
                    temperature REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()

    def save_temperature(self, pool_name, temperature):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('INSERT INTO temperatures (pool_name, temperature) VALUES (?, ?)', (pool_name, temperature))
        conn.commit()
        conn.close()

    def get_temperatures(self, pool_name , current_day = False):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if current_day:
            now = datetime.utcnow().replace(tzinfo=pytz.utc)
            start_of_day = now.astimezone(pytz.timezone('US/Mountain')).replace(hour=0, minute=0, second=0, microsecond=0)
            c.execute('SELECT timestamp, temperature FROM temperatures WHERE pool_name = ? AND timestamp >= ? ORDER BY timestamp', (pool_name, start_of_day))
        else:
            c.execute('SELECT timestamp, temperature FROM temperatures WHERE pool_name = ? ORDER BY timestamp', (pool_name,))
        data = c.fetchall()
        conn.close()
        return data

class TempApp(customtkinter.CTk):
    def __init__(self, db_manager):
        super().__init__()

        self.db_manager = db_manager

        #define pools
        self.pool_names = ["Big Pool", "Covered Pool", "Long Pool", "Short Pool", "Well"]
        # Create a dictionary to hold the entry widgets for each pool
        self.pool_entries = {}
        # Thresholds for temperature checks
        self.TEMPERATURE_THRESHOLDS = {
            "Big Pool": {"high": 98.5, "low": 88.0},
            "Covered Pool": {"high": 106.0, "low": 102.0},
            "Long Pool": {"high": 103.0, "low": 97},
            "Short Pool": {"high": 102.5, "low": 95.5},
            "Well": {"high": 112, "low": 95},
        }

        # Define ideal temperatures for each pool. 
        #I want to make this a seasonal thing, either winter or summer where the ideal temps change. 
        self.IDEAL_TEMPERATURES = {
            "Big Pool": 93.5,
            "Covered Pool": 104.0,
            "Long Pool": 100.0,
            "Short Pool": 99.0,
            "Well": 100.0,
        }

        #configure window
        self.title("Miracle Pool Temp Submission.py")
        self.geometry(f"{1000}x{500}")
       

        #configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        #create left sidebare with entry points. 
        self.frame_1 = customtkinter.CTkFrame(self, width=200, corner_radius=0)
        self.frame_1.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.frame_1.grid_rowconfigure(7, weight=1)
        self.label_1 = customtkinter.CTkLabel(master=self.frame_1, text="Miracle Pool Temps", justify=customtkinter.LEFT)
        self.label_1.grid(row=0, column = 0, pady=10, padx=10)
        for i, pool in enumerate(self.pool_names):
            entry = customtkinter.CTkEntry(master=self.frame_1, placeholder_text=pool)
            entry.grid(row=i+1, column=0, pady=10, padx=20)
            self.pool_entries[pool]=entry
        self.temp_submit_button = customtkinter.CTkButton(master=self.frame_1, text="Submit Temps", command=self.submit)
        self.temp_submit_button.grid(row=6, column=0, pady=10, padx=10)

        #Create center frame that spans two columns. 
        self.frame_2 = customtkinter.CTkFrame(self, width=600, height = 550, corner_radius=0)
        self.frame_2.grid(row=0, column=1, columnspan=2, sticky="nsew")
        self.graph_tab = customtkinter.CTkTabview(master=self.frame_2, width=600, height=450)
        self.graph_tab.grid(row=0, column=1, pady=40, padx=20)
        self.graph_canvases = {}
        for pool in self.pool_names:
            tab = self.graph_tab.add(pool)
            self.graph_canvases[pool] = self.create_graph(tab, pool)
        
        #Create third frame with random widgets
        self.frame_3 = customtkinter.CTkFrame(self, width=200, corner_radius=0)
        self.frame_3.grid(row = 0, column=3, rowspan=4, sticky="nsew")
        self.label_2 = customtkinter.CTkLabel(master=self.frame_3, text="Settings - TBD", justify=customtkinter.RIGHT)
        self.label_2.grid(row=0,column=3, pady = 10, padx=10)

        self.combobox_1 = customtkinter.CTkComboBox(master=self.frame_3, values=["Option 1", "Option 2", "Option 42 long long long..."])
        self.combobox_1.grid(row = 1, column=3, pady=10, padx=10)
        self.combobox_1.set("CTkComboBox")

        self.checkbox_1 = customtkinter.CTkCheckBox(master=self.frame_3)
        self.checkbox_1.grid(row = 2, column=3, pady=10, padx=10)

        self.switch_1 = customtkinter.CTkSwitch(master=self.frame_3)
        self.switch_1.grid(row = 3, column=3, pady=10, padx=10)

    def create_graph(self, tab, pool_name):
        fig, ax = plt.subplots(figsize = (5, 3))
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
        ax.set_title(pool_name)
        ax.set_xlabel('Timestamp')
        ax.set_ylabel('Temperature')
        self.update_graph(ax, pool_name)
        canvas.draw()
        return canvas
    
    def update_graph(self, ax, pool_name):
        data = self.db_manager.get_temperatures(pool_name, current_day=True)
        if data:
            timestamps, temperatures = zip(*data)
            mst = pytz.timezone('US/Mountain')
            timestamps = [datetime.strptime(ts, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc).astimezone(mst) for ts in timestamps]
            ax.clear()
            ax.plot(timestamps, temperatures, label= pool_name)
            ax.set_title(pool_name)
            ax.set_xlabel('Timestamp (MST)')
            ax.set_ylabel('Temperature')
            ax.legend()
            #set x-axis date format.
            date_format = DateFormatter('%H:%M', tz=mst)
            ax.xaxis.set_major_formatter(date_format)
            fig = ax.get_figure()
            fig.autofmt_xdate() #Auto-format the x axis labels for better readability.

            # Add a horizontal line for the ideal temperature
            ideal_temp = self.IDEAL_TEMPERATURES[pool_name]
            ax.axhline(y=ideal_temp, color='red', linestyle='--', label='Ideal Temperature')
            ax.legend()


    def submit(self):
        for pool_name in self.pool_entries:
            input_value = self.pool_entries[pool_name].get()
            #check if input is empty. 
            if input_value.strip()=="":
                tkinter.messagebox.showwarning("Entry Alert", f'Skipping {pool_name} due to empty field.')
                continue
            #Try to convert the string to a float. If not possible send message that  it is an invalid number. 
            try:
                temperature = float(input_value)
        
            except ValueError:
                tkinter.messagebox.showwarning("Entry Alert", f"Invalid input for {pool_name}: {input_value} is not a valid number.")
                continue
        
            #Proceed with using the temp variable. 
            # Check if temperature is too high or too low and display a message
            if temperature > self.TEMPERATURE_THRESHOLDS[pool_name]["high"]:
                tkinter.messagebox.showwarning("Temperature Alert", f"The {pool_name} is too warm, take measures to cool it down.")
            elif temperature < self.TEMPERATURE_THRESHOLDS[pool_name]["low"]:
                tkinter.messagebox.showwarning("Temperature Alert", f"The {pool_name} is too cold, take measures to warm it up.")
            
            self.db_manager.save_temperature(pool_name, temperature)
            self.pool_entries[pool_name].delete(0, tkinter.END)  #Clear the entry after saving

            #update the graph. 
            canvas = self.graph_canvases[pool_name]
            self.update_graph(canvas.figure.axes[0], pool_name)
            canvas.draw()




if __name__ == "__main__":
    #Get the direcroty where the script is located. 
    script_dir = os.path.dirname(os.path.abspath(__file__))
    #Define the database path relative to the script directory.
    db_path = os.path.join(script_dir, 'pool_temperatures.db')
    db_manager = DatabaseManager(db_path)
    app = TempApp(db_manager)
    app.mainloop()
