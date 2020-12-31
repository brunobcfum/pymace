#!/usr/bin/env python3

""" 
This is a scaffolded application. Implement any desired behaviour here.
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import sys, json, traceback, time, threading, asyncio, random
from apscheduler.schedulers.background import BackgroundScheduler
from classes import prompt

class App():

    def __init__(self, Node, tag, time_scale, second):
        'Initializes the properties of the Node object'
        #### Genesis Common 
        random.seed(tag)
        self.Node = Node
        self.tag = tag
        self.tag_number = int(self.tag[5:])
        self.debug = False
        self.multiplier = time_scale
        self.scheduler = BackgroundScheduler()
        ### Application variables
        ##################### Constructor actions  #########################
        self._setup()

    ############# Public methods ########################

    def start(self):
        self.scheduler.start()
        self._auto_job()

    def shutdown(self):
        self.scheduler.shutdown()

    def toggleDebug(self):
        self.debug = not self.debug
        if (self.debug): 
            print("MyApp -> Debug mode set to on")
        elif (not self.debug): 
            print("MyApp -> Debug mode set to off")

    def printinfo(self):
        'Prints general information about the application'
        print()
        print("Application stats (MyApp)")
        print("Role: \t\t" + self.Node.role)
        print()

    ############# Private methods #######################

    def _setup(self):
        settings_file = open("./classes/apps/myapp/settings.json","r").read()
        settings = json.loads(settings_file)
        self.sample = settings['sample']

    def _auto_job(self):
        'Loads batch jobs from files. File must correspond to node name'
        try:
            jobs_file = open("./classes/apps/myapp/job_" + self.Node.tag + ".json","r").read()
            jobs_batch = json.loads(jobs_file)
            loop = asyncio.get_event_loop()
            for job in jobs_batch["jobs"]:
                loop.create_task(self._auto_job_add(job['start'],job['type'],job['value']))
            loop.run_forever()
            loop.close()
        except:
            #print("No jobs batch for me")
            pass

    async def _auto_job_add(self, delay, jobtype, value):
        'Adds batch jobs to the scheduler'
        await asyncio.sleep(delay * self.Node.multiplier)
        self._add_job(jobtype, value)

    def _add_job(self, jobtype='help', value=None):
        'Adds manual jobs'
        if jobtype == 'help':
            try:
                self._printhelp()
            except:
                traceback.print_exc()

    def _prompt(self, command):
        if (len(command))>=2:
            if command[1] == 'help':
                self._printhelp()
            else:
                print("Invalid Option")
                self._printhelp()
        elif (len(command))==1:
            self._printhelp()

    def _printhelp(self):
        'Prints general information about the application'
        print()
        print("Options for My Application")
        print()
        print("help                - Print this help message")
        print()
