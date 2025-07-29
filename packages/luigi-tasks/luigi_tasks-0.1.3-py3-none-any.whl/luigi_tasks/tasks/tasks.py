import luigi
import logging
import time
logger = logging.getLogger('luigi-interface')

class HelloTask(luigi.Task):
    """A simple task that prints 'Hello, World!'"""
    
    def run(self):
        time.sleep(10)
        logger.info("Hello, World!")
        
    def output(self):
        return luigi.LocalTarget('hello.txt')
        
    def complete(self):
        return self.output().exists()

class PrintTask(luigi.Task):
    """A task that prints a custom message"""
    
    message = luigi.Parameter(default="Default message")
    
    def run(self):
        time.sleep(10)
        logger.info(f"Printing message: {self.message}")
        with self.output().open('w') as f:
            f.write(self.message)
            
    def output(self):
        return luigi.LocalTarget(f'print_{self.message.replace(" ", "_")}.txt')
        
    def complete(self):
        return self.output().exists() 