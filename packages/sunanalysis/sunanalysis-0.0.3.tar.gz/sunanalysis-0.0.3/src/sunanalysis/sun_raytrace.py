from ladybug_geometry.geometry3d import Mesh3D,Face3D,Ray3D,LineSegment3D,Plane,Polyline3D,Vector3D,Point3D
from ladybug_geometry.intersection3d import intersect_line3d_plane
from ladybug_geometry.geometry2d import Point2D,Polygon2D,Mesh2D
from ladybug.sunpath import Sunpath,Sun
from ladybug.epw import EPW
import math





from sunanalysis.util import *



def intersect_line3d_mesh(ray:Ray3D,mesh:Mesh3D)->(Point3D|None,int|None):
    l_mesh_faces=mesh.faces
    planes=[p.plane() for p in l_mesh_faces]
    for index, p in enumerate(planes):
        inter=intersect_line3d_plane(ray,p)
        if inter!=None:
            return inter,index
    return None,None

"""
class ReflectOnGround(object):
    def __init__(self,reflect_rec:[Polyline],reflectvector:[[Vector3d]],reflect_value,mesh:Mesh,curtain_wall:Mesh):
        self.reflect_rec = reflect_rec
        self.reflectvector = pd.DataFrame(reflectvector)
        self.reflect_value = reflect_value
        self.mesh = mesh
        self.is_include=True
        self.curtain_wall = curtain_wall

    def Cells(self)->[int]:
        return None
    def rayOnMesh(self,rec:Polyline, vector:Vector3d, mesh:Mesh):
        Line=[]
        ps = [p for p in rec]
        ps.pop(-1)
        # reflected corner in ground
        newp = []
        lmesh=rmesh_to_lmesh(mesh)

        for p in ps:
            ray = Ray3D(p,vector)

            p,index = intersect_line3d_mesh(ray,lmesh)
            if p==None:
                pass
            else:
                newp.append(p)

        if len(newp) < 3:
            return []
        newp.append(newp[0])
        # create polygone on ground
        poly =Polyline3D(newp).to_polyline2d().to_polygon(1)
        Line.append(poly)
        # find mesh index in projected poly
        meshcenters=lmesh.face_centroids
        indexs=[]
        for index, p in enumerate(meshcenters):
            result=poly.point_relationship(p,1)
            if result==1:
                indexs.append(index)
        return indexs


    def raysOnMesh(self,rays):
        # reflect rays per time. rays from differnt glass panel
        rendervalue=[{i:0} for i in range(0,self.mesh.Faces.Count)]
        for index, r in enumerate(rays):
            index = self.rayOnMesh(self.reflect_rec[index], r, self.mesh)
            for _i in index:
                rendervalue[_i] += 1
                # create append cell
                #Cells[_i].reflect_vector.append(r)

        return rendervalue
    def run(self):
        for i in self.reflectvector:
            if self.is_include:
                iu = self.reflect_value[i]
                if iu > 4000:
                    self.raysOnMesh(self.reflectvector[i])
            else:
                self.raysOnMesh(self.reflectvector[i])

"""
class GlareReflectionArea(object):
    def __init__(self,mesh:Mesh,input_vectors):
        self.mesh = mesh
        self.mesh_normals=mesh.Normals
        self.mesh_vertices=mesh.Vertices
        self.mesh_faces=mesh.Faces
        self.input_vectors = input_vectors
    def Cells(self)->[int]:
        return None

    def reflect_rec(self):
        _mesh=Mesh3D(rpointf_to_lpoint(self.mesh_vertices),self.mesh_faces)
        edges=_mesh.edges

        print(edges)



        return _mesh
    def reflect_vectors(self):

        return None


class AshraeSky():
    """
    室外照度模型
    """
    def __init__(self,latitude:float,reflection:float,h:[]):
        self.latitude=latitude
        #reflection is 反射率
        self.reflection=reflection
        self.h=h
    @staticmethod
    def EE(h, A=1.37):
        if h > 0:  # 太阳在地平线上
            try:
                _E = (A * 10 ** 5) * math.exp(-0.223 / math.sin(math.radians(h)))
            except:
                _E = 0
        else:
            _E = 0

        return _E
    @staticmethod
    def liangdu(fanshe, E):
        return fanshe * E / math.pi
    def luxvalue(self)->[float]:
        """
        return lux value by h
        :return:
        """
        lux_value=[]
        result=[]
        for _h in self.h:
            _E = self.EE(_h)
            lux_value.append(_E)
            _result = self.liangdu(self.reflection, _E)
            result.append(_result)
        return  lux_value

class CalResult():
    """
    Stu to save Reflection result. Store analysied face and panel face paires.
    """
    def __init__(self,mesh:Mesh3D|None,glassindex:int,analysismeshindex:list[int],analysismeshindex2:list[int],sunindex:int):
        self.m=mesh
        #self.ismid=ismid
        #self.overlay=overlay
        self.glassindex=glassindex
        self.analysismeshindex=analysismeshindex
        self.analysismeshindex2=analysismeshindex2
        self.sunindex=sunindex



class CalReflection():
    """
    glass and input_vector one vs one
    """
    def __init__(self,glassface:Face3D,glassindex:int,sun:Sun,sunindex:int,latitude:float,glassreflection:float=0.15):
        self.glassface=glassface

        self.input_vecotr=sun.sun_vector
        self.sun=sun
        self.sunindex=sunindex
        self.glassindex=glassindex
        self.latitude=latitude
        self.glassreflection=glassreflection
    def sunisabove(self):
        """
        to test is sun point in the side of reflection
        :return:
        """
        plane=self.glassface.plane
        sunpoint=self.sun.position_3d()
        if plane.is_point_above(sunpoint):
            return True
        else:
            return False
    def filertsun(self,max=4000):
        """
        test sun lunmiance value
        :return:
        """
        sky=AshraeSky(self.latitude,self.glassreflection,[self.sun.altitude])
        glarevalue=sky.luxvalue()[0]
        if glarevalue > max:
            return True
        else:
            return False
    def input_rays(self)->[Ray3D]:
        """
        get input ray for each glass panel corner
        :return:
        """
        ps=self.glassface.vertices
        rays=[Ray3D(p,self.input_vecotr) for p in ps]
        return rays
    def reflect_rays(self)->[Ray3D]:
        """
        get reflect ray for each glass panel corner
        :return:
        """
        plane=self.glassface.plane
        ps=self.glassface.vertices
        input_rays=self.input_rays()
        reflect_rays=[]
        for index, ray in enumerate(input_rays):
            _ray=ray.reflect(plane.n,ps[index])
            reflect_rays.append(_ray)
        return reflect_rays
    @staticmethod
    def testresult(projectpolygon:Polygon2D,analysisedpolygon:Polygon2D):

        center=analysisedpolygon.center
        includemid=projectpolygon.is_point_inside(center)
        _overlap = projectpolygon.polygon_relationship(analysisedpolygon, 1)
        return includemid , _overlap!=-1

    def reflect_polyone(self,analysismesh:Mesh3D)->CalResult:
        """
        glass panel reflect to the analysismesh and save the result of cal
        :param analysismesh:
        :return:
        """
        # exclude the ray not reach the lux min,and ray at the backside of panel
        if self.filertsun()!=True or self.sunisabove()!=True:
            return CalResult(None,self.glassindex,[],[],self.sunindex)
        #get all reflect rays
        reflect_rays=self.reflect_rays()
        plane=Face3D(analysismesh.face_edges[0]).plane

        ps=[plane.intersect_line_ray(r) for r in reflect_rays]
        # if any point can not project to analysied mesh,return
        if None in ps:
            return CalResult(None,self.glassindex,[],[],self.sunindex)
        else:
            polyline=Polyline3D(ps)
            polyline2d=polyline.to_polyline2d().to_polygon(1)
            index=[]
            _index=[]
            #test if analysised center inside project polygon
            for _i,f in enumerate(analysismesh.face_edges):
                _f2d=f.to_polyline2d().to_polygon(1)
                ismid,_overlap=self.testresult(polyline2d,_f2d)
                if ismid:
                    _index.append(_i)
                if _overlap:
                    index.append(_i)
            _m = Mesh3D(polyline.vertices, [(0, 1, 2, 3)])
            return CalResult(_m,self.glassindex,_index,index,self.sunindex)

class Glare_Analysis():
    def __init__(self,epwpath:str, hoys:[int],building:Mesh3D,analysisgird:Mesh3D,selectedindex:[]):
        self.epw=EPW(epwpath)
        self.hoys=hoys
        self.building=building
        self.analyaisgird=analysisgird
        self.selectedindex=selectedindex
        self.sunpath=Sunpath(self.epw.location.latitude,self.epw.location.longitude,self.epw.location.time_zone)
    def sun(self)->[Sun]:
        """
        get sun by hoys
        :return:
        """
        sun=[self.sunpath.calculate_sun_from_hoy(h) for h in self.hoys]
        return sun
    def luxvalues(self)->[float]:
        """
        get lux value
        :return:
        """
        ashrae=AshraeSky(self.epw.location.latitude,0.15,[s.altitude for s in self.sun()])

        return ashrae.luxvalue()
    def luxvalue(self,index)->float:
        """
        get lux value
        :return:
        """
        ashrae=AshraeSky(self.epw.location.latitude,0.15,[s.altitude for s in self.sun()[index]])

        return ashrae.luxvalue()[0]

    @staticmethod
    def plane_reflect(p:Plane,v:Vector3D)->Ray3D:
        ray=Ray3D(p.o,v)

        return ray.reflect(p.n,p.o)

    @staticmethod
    def planes_reflect(ps:[Point3D],ray:Vector3D)->[Ray3D]:
        rays=[]
        plane=Plane.from_three_points(ps[0],ps[1],ps[2])
        for p in ps:
            _v=p-ps[0]
            _plane=plane.move(_v)
            _ray=Glare_Analysis.plane_reflect(_plane,ray)
            rays.append(_ray)
        return rays

    @staticmethod
    def rays_project_mesh(rays:[Ray3D],amesh:Mesh3D)->Mesh3D|None:

        plane=Face3D(amesh.face_edges[0]).plane

        ps=[plane.intersect_line_ray(r) for r in rays]
        try:
            polyline=Polyline3D(ps)
            _m = Mesh3D(polyline.vertices, [(0, 1, 2, 3)])
            return _m
        except:
            return None

    @staticmethod
    def to3dmfile(meshs: [Mesh3D],resultindex,resultindex2):
        rmesh = lmeshs_to_rmeshs(meshs)
        _to = {}
        for index, m in enumerate(rmesh):
            if m != None:
                _to[index] = m
            else:
                continue
        dmbtye = write3dm(_to, {"meshindex": resultindex,"glassindex": resultindex2})
        return dmbtye

    def analysis_to_glass(self,result:list[CalResult],analysismeshindex:list[int])->list[int]:
        _r=[0 for i in self.building.faces]
        for index,r in enumerate(result):
            for a_index in analysismeshindex:
                if a_index in r.analysismeshindex2:
                    _r[r.glassindex]+=1
        return _r

    def glass_to_analysis(self,result:list[CalResult])->list[int]:
        result_index = [0 for i in self.analyaisgird.face_centroids]

        for i in result:
            for index in i.analysismeshindex:

                result_index[index] += 1
        return result_index



