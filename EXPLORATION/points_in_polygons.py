"""helper skript with methodes to count points in polygons 

functions:
    * if_point_inpolygon - returns True/False ... simple check
    * count_points_in_polygon - returns an int value .. that is a count of points from a list in one polygon
    * count_points_in_polygonlist - returns an list with int values .. that is a count of points from a list in a list of polygons
"""

from shapely.geometry import Point, Polygon


#return True/False
def if_point_inpolygon(polygon, point):
    """method required one polygon and one point to check the point in a polygon
    
        Parameters
        ----------
        polygon : shapely.geometry.Polygon
            One Polygon with Points 
        point : shapely.geometry.Point
            One Point with (x,y)
        
        Returns
        -------
        bool
            ist the point in poolygon .. Ture or False
        """
    
    point = Point(point)
    return point.within(polygon)
        

def count_points_in_polygon(polygon, pointlist):
    """method required one polygon and a pointlist to count the points in a polygon
       
       Parameters
        ----------
        polygon : shapely.geometry.Polygon
            One Polygon with Points 
        pointlist : [shapely.geometry.Point]
            A List of Points with [(x1,y1),..,(xn,yn)]
    
        Returns
        -------
        int
            the of the points in polygon
        """
    
    return [if_point_inpolygon(polygon,point) for point in pointlist].count(True)

def count_points_in_polygonlist(polygonlist, pointlist):
    """method required polygonlist and pointlist to count the points in polygons
    
       Parameters
        ----------
        polygonlist : [shapely.geometry.Polygon]
            A List of Polygons with [((x1,y1),..,(xn,yn)),((x1,y1),..,(xn,yn))] 
        pointlist : [shapely.geometry.Point]
            A List of Points with [(x1,y1),..,(xn,yn)]
        
        Returns
        -------
        list
            a list of int values 
    """
    
    #TODO: make a listcomp...
    countliste = []
    for polygon in polygonlist:
        countliste.append([if_point_inpolygon(polygon,point) for point in pointlist].count(True))
    return countliste