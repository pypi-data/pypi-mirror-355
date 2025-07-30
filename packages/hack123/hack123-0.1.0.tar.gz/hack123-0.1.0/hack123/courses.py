class Course:
    def __init__(self, name, duration, link):
        self.name = name
        self.duration = duration
        self.link = link
    
    def __str__(self):
        return f"El curso {self.name} dura {self.duration}, Link : {self.link}"

courses = [
    Course("Intrudoccion a Linux", 15, "www.google.com"),
    Course("Personalizacion de Linux", 3 , "www.google.com"),
    Course("Introduccion al Hacking", 53, "www.google.com")
]
def list_courses():
    for course in courses:
        print(course)

def search_course_byname(name):
    for course in courses:
        if course.name == name:
            return course
    return None
