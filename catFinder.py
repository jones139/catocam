# Abstract cat finder class - different algorithms will inherit from this class 
# to provide a consistent interface

class CatFinder:
    ''' 
    CatFinder is an abstract class to provide a standard interface to a cat finding model.
    '''
    def __init__(self, settingsObj, debug):
        '''
        Initialise the model
        '''
        print("CatFinder.__init__")
        self.settingsObj = settingsObj
        self.debug = debug

    def findCat(self, img):
        '''
        Analyse image img to determine whether or not it contains a cat
        Return a tuple (catFound, catData) where catFound is a boolean to indicate
        whether or not a cat has been found in the image, and catData is an object
        of information regarding the model results (which may vary by model)
        '''
        print("CatFinder.findCat() - img="+img)

    def getAnnotatedImage(self, img):
        '''
        Returns the image annotated with the detected objects
        '''
        print("CatFinder.getAnnotatedImage() - img="+img)

