import os
import sys
import json
import datetime
from tkinter import *
from math import copysign

class UIWindow(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title('Critterpedia Companion')
        self.optionroot = Frame(self)
        self.optionroot.pack()
        
        self.hemisphereframe = Frame(self.optionroot)
        self.hemispheremod = IntVar(value=0)
        Radiobutton(self.hemisphereframe, text='Northern', variable=self.hemispheremod, value=0, command=self.refresh).grid(row=0, column=0)
        Radiobutton(self.hemisphereframe, text='Southern', variable=self.hemispheremod, value=6, command=self.refresh).grid(row=0, column=1)
        self.hemisphereframe.pack()
        
        self.searchterm = StringVar()
        self.searchbox = Entry(self.optionroot, textvariable=self.searchterm)
        self.searchbox.bind ("<Return>", lambda _: self.searchdata(self.searchterm.get().lower()))
        self.searchbox.pack()
        
        self.hideunavailable = BooleanVar(value=True)
        Checkbutton(self.optionroot, text='Hide unavailable', variable=self.hideunavailable, command=self.refresh).pack()
        self.hidecaught = BooleanVar(value=True)
        Checkbutton(self.optionroot, text='Hide caught', variable=self.hidecaught, command=self.refresh).pack()

        Button(self.optionroot, text='Refresh', command=self.refresh).pack()
        
        Label(self, text='Available critters:').pack()
        self.dataroot = Frame(self, bd=2, relief=SUNKEN)
        self.dataroot.grid_rowconfigure(0, weight=1)
        self.dataroot.grid_columnconfigure(0, weight=1)
        self.datascrollbar = Scrollbar(self.dataroot)
        self.datascrollbar.grid(row=0, column=1, sticky=N+S)
        self.datacanvas = Canvas(self.dataroot, bd=0, yscrollcommand=self.datascrollbar.set, width=800)
        self.datacanvas.grid(row=0, column=0, sticky=N+S+E+W)
        self.datascrollbar.config(command=self.datacanvas.yview)
        def on_mousewheel(event):
            self.datacanvas.yview_scroll(int(copysign(1, -event.delta)), "units")
        self.datacanvas.bind_all("<MouseWheel>", on_mousewheel)
        self.dataroot.pack(fill="both", expand=True)

        self.dataframe = Frame(self.datacanvas)
        def fixcanvas(event):
            self.datacanvas.configure(scrollregion=self.datacanvas.bbox("all"))
        self.dataframe.bind("<Configure>",fixcanvas)
        self.datacanvas.create_window((0,0),window=self.dataframe,anchor='nw')

        self.refresh()
        self.mainloop()
        
    def drawdata(self, available, gonesoon):
        self.datarows = {}
        for column, header in enumerate(("Catch", "Name", "Value", "Months", "Time", "Location", "Size")):
            Label(self.dataframe, text=header).grid(row=0, column=column)
        for row, critter in enumerate(available, start=1):
            if critter in gonesoon:
                fgcolor = "red"
            else:
                fgcolor = "black"
            self.datarows[critter] = self.datarow(self.dataframe, critter, row, fgcolor)
        
    def refresh(self):
        if self.hideunavailable.get():
            month = self.hemispheremod.get() + datetime.date.today().month #datetime.datetime.now().month
            self.available, self.gonesoon = getavailable(month, self.hidecaught.get())
        else:
            self.available = critterdata.keys()
            self.gonesoon = []
        self.searchdata("")

    def deleterow(self, critter):
        if self.hidecaught.get():
            for child in self.datarows[critter]:
                child.destroy()
        else:
            self.datarows[critter][0]["state"] = DISABLED
            self.datarows[critter][0]["text"] = "Caught"
            for child in self.datarows[critter]:
                child["fg"] = "gray50"
        
    def datarow(self, parent, critter, row, fgcolor):
        rowelements = []
        rowelements.append(Button(parent, text='Catch', command=lambda critter=critter: [addcritter(critter), self.deleterow(critter)]))
        if critter in mycritters:
            rowelements[0]["state"] = DISABLED
            rowelements[0]["text"] = "Caught"
            fgcolor = "gray50"
        rowelements.append(Label(parent, text=critter, fg=fgcolor))
        rowelements.append(Label(parent, text=critterdata[critter]["Value"], fg=fgcolor))
        rowelements.append(Label(parent, text=converttimesets(critterdata[critter]["Months"], "%m", "%b", self.hemispheremod.get()), fg=fgcolor))
        rowelements.append(Label(parent, text=converttimesets(critterdata[critter]["Time"], "%H", "%I%p", 0), fg=fgcolor))
        rowelements.append(Label(parent, text=critterdata[critter]["Location"], fg=fgcolor))
        try:
            rowelements.append(Label(parent, text=critterdata[critter]["Size"], fg=fgcolor))
        except KeyError:
            pass
        for column, element in enumerate(rowelements):
            element.grid(row=row, column=column)
        return rowelements
    
    def searchdata(self, searchterm):
        if searchterm == "":
            searchresults = self.available
        else:
            searchresults = []
            for critter in self.available:
                if searchterm in critter.lower():
                    searchresults.append(critter)
        for child in self.dataframe.winfo_children():
            child.destroy()
        self.drawdata(searchresults, self.gonesoon)
        self.datacanvas.yview_moveto(0)
        

def whatcatch():
    month = datetime.date.today().month #datetime.datetime.now().month
    thismonth, gonesoon = getavailable(month, True)

    if len(thismonth) > 0:
        print("The following uncaught critters are available to catch this month:")
        for critter in thismonth:
            printcritterdata(critter)
    
        if len(gonesoon) > 0:
            print()
            print("The following uncaught critters will be gone at the end of the month:")
            for critter in gonesoon:
                printcritterdata(critter)
    else:
        print("There is nothing new to catch this month. Good job!")
    print()

def getavailable(month, filter=False):
    availablrcrits = [[],[]]
    for critter in critterdata:
        if not filter or critter not in mycritters: #if we don't have the bug/fish
            for months in critterdata[critter]["Months"]: #Merge this and below into> #for months in filter(lambda x: inrange(month, x, True), critterdata[critter]["Months"]):
                if inrange(month, months, True): #it's available to catch
                    availablrcrits[0].append(critter)
                    if not inrange(month, months, False): #if it won't be available next month
                        availablrcrits[1].append(critter)
    return availablrcrits

def addcritter(critter):
    mycritters.append(critter)
    writefile(mycrittersjson, sorted(mycritters))

def converttimesets(timesets, inputf, outputf, hemispheremod):
    return ' & '.join(['-'.join([formattime(time, inputf, outputf, hemispheremod) for time in timeset]) for timeset in timesets])

def formattime(time, inputf, outputf, hemispheremod):
    try:
        if hemispheremod > 0:
            time = ((time + hemispheremod) % 12)
            if time == 0:
                time = 12
        return datetime.datetime.strptime(str(time), inputf).strftime(outputf)
    except (ValueError, TypeError):
        return str(time)
    
def readfile(file, default=None):
    try:
        with open(file, "r") as f:
            return json.loads(f.read())
    except FileNotFoundError:
        if default is not None:
            return default
        else:
            print("ERROR: \"" + file + "\" not found!")
            raise SystemExit

def writefile(file, data):
    with open(file, "w") as f:
        f.write(json.dumps(data, indent="\t", sort_keys=True))

def inrange(num, range, inclusive=False):
    try:
        if range[0] < range[1]:
            return num >= range[0] and num < range[1] + inclusive
        elif range[0] > range[1]: # crosses midnight/newyear
            return num >= range[0] or num < range[1] + inclusive
    except IndexError: # if there isn't a proper range, check if it's a single value range that matches the input, or if it's a string
        return num == range[0] or type(range[0]) == str


mycrittersjson = os.path.join(sys.path[0], "MyCritters.json")
mycritters = readfile(mycrittersjson, [])
critterdatajson = os.path.join(sys.path[0], "CritterData.json")
critterdata = readfile(critterdatajson)

window=UIWindow()
