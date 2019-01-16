class BasicFilter(object):

    def filter(self,target_list):
        """
            Filters the list of targets.
            A filter may re-order the items,
            and also remove items from the list.
        """
        for t in target_list:
            self.filter_single(t)

    def filter_single(self,target):
        pass

class FilterListFilter(object):
    def __init__(self,filter_list):
        self.filter_list = filter_list

    def filter(self,target_list):
        for f in self.filter_list:
            f.filter(target_list)

class YCoordinateFilter(BasicFilter):
    def __init__(self,min_y, max_y):
        self.min_y = min_y
        self.max_y = max_y

    def filter_single(self,target):
        target_y = target.center()[1]

        if target_y >= self.min_y and target_y <= self.max_y:
            target.accept()
        else:
            target.reject("y=%d is not between %d and %d" % (target_y,self.min_y,self.max_y))
            
class AspectRatioFilter(BasicFilter):
    def __init__(self,min_ar=0.0,max_ar=0.0)
        self.min_ar = min_ar
        self.max_ar = max_ar
    def filter_single(self,target):
        ar = target.bounding_rect.aspect_ratio()
        if ar >= self.min_ar and ar <= self.max_ar:
            target.accept()
        else:
            target.reject("ar=%d is not between %d and %d" % (ar,self.min_ar,self.max_ar))

class VertextCountFilter(BasicFilter):
    def __init__(self,min_vertices, max_vertices):
        self.min_vertices = min_vertices
        self.max_vertices = max_vertices

    def filter_single(self,target):
        v = target.num_vertices
        if v <= self.max_vertices and v >= self.min_vertices:
            target.accept()
        else:
            target.reject("vertices=%d is not between %d and %d" % (v,self.max_vertices,self.min_vertices))

class AreaFilter(BasicFilter):
    def __init__(self,min_area):
        self.min_area = min_area

    def filter_single(self,target):
        area = target.bounding_rect.area()
        if area >= self.min_area:
            target.accept()
        else:
            target.reject("area=%d is not at least %d " % (area,self.min_area))
