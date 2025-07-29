import numpy as np
import math

class boxfit:
    """
    MATHUSLA 10cm resolution fit
    
    Attributes:
        l_weights (list): Weights for sub-volumes along volumes length.
        l_step (int): Step size for length sub-volumes.
        w_weights (list): Weights for sub-volumes along volumes width.
        w_step (int): Step size for width sub-volumes.
        h_weights (list): Weights for sub-volumes along volumes height.
        h_step (int): Step size for height sub-volumes.
        orientation (list): Orientation of the volumes in ['x', 'y', ...] order. Allows for rotation in x-y plane
        spacing (list): List of vertical spacings between volumes.
        verbose (int): Verbosity level for debugging output.
    """
    def __init__(self, **kwargs):
        """
        Initializes the class object with optional parameters.

        Args:
            **kwargs: Arbitrary keyword arguments for customizing weights, step size, orientation, spacing, and verbosity.
        """
        self.l_weights = kwargs.get('l_weights', [0.05, 0.27, 0.73, 0.95, 1, 1, 1, 1, 1, 0.95, 0.73, 0.27, 0.05])
        self.l_step = kwargs.get('l_step', 2)
        self.w_weights = kwargs.get('w_weights', [0.05, 1, 1, 0.05])
        self.w_step = kwargs.get('w_step', 2)
        self.h_weights = kwargs.get('h_weights', [1])
        self.h_step = kwargs.get('h_step', 1)
        self.orientation = kwargs.get('orientation', ['x', 'y', 'x', 'y'])
        self.spacing = kwargs.get('spacing', [80, 80, 80])
        self.verbose = kwargs.get('verbose', 0)

    def define_lines(self,hitlist):
        """
        Generates potential lines between hit points using the defined weights and steps.

        Args:
            hitlist (list): A list of hit points containing coordinates ('x', 'y', 'z').

        Returns:
            list: A list of fit weighted fit lines defined at a central point [[x,y,z,thetax,thetay,weight],...]
        """
        bottom = hitlist[0]
        top = hitlist[-1]

        zlow=bottom['z']
        zhigh=top['z']

        if(zhigh-zlow != sum(self.spacing)):
            print("zlow:",zlow," zhigh:",zhigh)
            print("spacing:",self.spacing)
            raise ValueError("Spacing between layers does not match defined spacing")

        bot_x_step=0
        bot_x_weights=[]
        bot_y_step=0
        bot_y_weights=[]
        bot_z_step=0
        bot_z_weights=[]
        
        top_x_step=0
        top_x_weights=[]
        top_y_step=0
        top_y_weights=[]
        top_z_step=0
        top_z_weights=[]
        
        if(self.orientation[0]=='x'):
            bot_x_step=self.l_step
            bot_x_weights=self.l_weights
            bot_y_step=self.w_step
            bot_y_weights=self.w_weights
            bot_z_step=self.h_step
            bot_z_weights=self.h_weights
        elif(self.orientation[0]=='y'):
            bot_x_step=self.w_step
            bot_x_weights=self.w_weights
            bot_y_step=self.l_step
            bot_y_weights=self.l_weights
            top_z_step=self.h_step
            top_z_weights=self.h_weights
        else: ValueError("only x and y orientations are currently supported")
        if(self.orientation[-1]=='x'):
            top_x_step=self.l_step
            top_x_weights=self.l_weights
            top_y_step=self.w_step
            top_y_weights=self.w_weights
            top_z_step=self.h_step
            top_z_weights=self.h_weights
        elif(self.orientation[-1]=='y'):
            top_x_step=self.w_step
            top_x_weights=self.w_weights
            top_y_step=self.l_step
            top_y_weights=self.l_weights
            top_z_step=self.h_step
            top_z_weights=self.h_weights
        else: ValueError("only x and y orientations are currently supported")

        bot_x_edge=bottom['x']-bot_x_step*math.floor(len(bot_x_weights)/2.0)
        bot_y_edge=bottom['y']-bot_y_step*math.floor(len(bot_y_weights)/2.0)
        top_x_edge=top['x']-top_x_step*math.floor(len(top_x_weights)/2.0)
        top_y_edge=top['y']-top_y_step*math.floor(len(top_y_weights)/2.0)

        fit_lines=[]
        for bxid in range(len(bot_x_weights)):
            for byid in range(len(bot_y_weights)):
                for txid in range(len(top_x_weights)):
                    for tyid in range(len(top_y_weights)):
                
                        bot_x=bot_x_edge+bxid*bot_x_step
                        bot_y=bot_y_edge+byid*bot_y_step
                        top_x=top_x_edge+txid*top_x_step
                        top_y=top_y_edge+tyid*top_y_step

                        xave=(bot_x+top_x)/2.0
                        yave=(bot_y+top_y)/2.0
                        zave=(top['z']+bottom['z'])/2.0

                        vec=[top_x-bot_x,top_y-bot_y,top['z']-bottom['z']]

                        #theta=np.arccos(vec[2]/np.sqrt(vec[0]**2+vec[1]**2+vec[2]**2))
                        #phi=np.arctan2(vec[1],vec[0])
                        thetax=np.arccos(vec[0]/np.sqrt(vec[0]**2+vec[2]**2))
                        thetay=np.arccos(vec[1]/np.sqrt(vec[1]**2+vec[2]**2))

                        fit=[xave,yave,zave,thetax,thetay]

                        weight=self.get_weights(fit,hitlist)
                       
                        #oldweight=self.l_weights[bxid]*self.l_weights[byid]*self.t_weights[txid]*self.l_weights[tyid]
                        #weight=1 #TEST
                
                        if((self.verbose==1 and weight==1) or (self.verbose==2 and weight>0) or self.verbose==3):
                            print("test point:")
                            print("bottom: x:",bot_x," y:",bot_y)
                            print("top: x:",top_x," y:",top_y)
                            print("averages: x:",xave," y:",yave)
                            print("vector:", vec)
                            print("angles: x",thetax," y:",thetay) 
                            print("weight:",weight)
                            print("")
                            print("")
                    
                        #points.append([xave,yave,theta,phi,self.l_weights[i]*self.l_weights[j]])
                        if(weight>0): fit_lines.append(fit+[weight])

        return fit_lines
    def get_weights(self,fit,hits):
        """
        Calculates the weight of a line crossing through each layer
        
        Args:
            fit (list): [x,y,z,thetax,thetay] for the central fit point
            hists (list): list of all hits in event
        Returns:
            weight: weight for this fit line
        """
        weight=1
 #       for layer in hits:
        for layerid in range(len(hits)):
            x=hits[layerid]['x']
            y=hits[layerid]['y']
            z=hits[layerid]['z']
            intersect=self.get_layer_intersect(fit,z) #[x,y]
            xdist=round(abs(intersect[0]-x))
            ydist=round(abs(intersect[1]-y))
            if(self.orientation[layerid]=='x'):
                xbin=math.floor(xdist/self.l_step)
                xmid=math.floor(len(self.l_weights)/2.0)
                if(xbin>xmid): weight=0
                else: weight=weight*self.l_weights[xmid-xbin]
                ybin=math.floor(ydist/self.w_step)
                ymid=math.floor(len(self.w_weights)/2.0)
                if(ybin>ymid): weight=0
                else: weight=weight*self.w_weights[ymid-ybin]
                #print("xdist:",xdist," xbin:",xbin," ydist:", ydist," ybin:",ybin," weight:",weight)
            elif(self.orientation[layerid]=='y'):
                xbin=math.floor(xdist/self.w_step)
                xmid=math.floor(len(self.w_weights)/2.0)
                if(xbin>xmid): weight=0
                else: weight=weight*self.w_weights[xmid-xbin]
                ybin=math.floor(ydist/self.l_step)
                ymid=math.floor(len(self.l_weights)/2.0)
                if(ybin>ymid): weight=0
                else: weight=weight*self.l_weights[ymid-ybin]
            else: ValueError("bad z values")    
        return weight
    def get_layer_intersect(self,fit,z):
        zval=z-fit[2]
        xval=fit[0]+zval/np.tan(fit[3])
        yval=fit[1]+zval/np.tan(fit[4])
        return [xval,yval]
  

    def average_lines(self, linelist):
        """
        Calculates the weighted average and covariance matrix of the fit.

        Args:
         linelist (list): A list of lines with their attributes and weights.

        Returns:
            list: A list containing averages and covariance matrix.
        """
        evtsize = 5  # 6 entries - 1 weight = 5 variables
        averages = np.zeros(evtsize)
        sum_weights = sum([row[-1] for row in linelist])
    
        # Calculate weighted averages
        for entry in linelist:
            for val in range(evtsize):
                if self.verbose == 3:
                    print("average values")
                    print("index:", val)
                    print("value:", entry[val], " weight", entry[evtsize])
                    print("event:", entry)
                    print("running average:", averages[val])
                    print("")
                averages[val] += entry[val] * entry[evtsize] / sum_weights
        
        # Initialize covariance matrix
        covariance_matrix = np.zeros((evtsize, evtsize))
        
        # Calculate covariance matrix
        for entry in linelist:
            for i in range(evtsize):
                for j in range(evtsize):
                    covariance_matrix[i][j] += (entry[evtsize] / sum_weights) * \
                                               (entry[i] - averages[i]) * (entry[j] - averages[j])
        
        return [averages, covariance_matrix]

#   def average_lines(self, linelist):
#       """
#       Calculates the weighted average and standard deviation of the fit.

#       Args:
#           linelist (list): A list of lines with their attributes and weights.

#       Returns:
#           list: A list containing averages and standard deviations.
#       """
#       evtsize=5 #6 entries-1 weight = 5 variables
#       averages = np.zeros(evtsize)
#       stddev = np.zeros(evtsize)
#       sum_weights = sum([row[-1] for row in linelist])
#       for entry in linelist:
#           for val in range(len(entry[:evtsize])):
#               if(self.verbose==3):
#                   print("average values")
#                   print("index:",val)
#                   print("value:",entry[val]," weight",entry[evtsize])
#                   print("event:",entry)
#                   print("running average:",averages[val])
#                   print("")
#               averages[val]+=entry[val]*entry[evtsize]/sum_weights
#       for entry in linelist:
#           for val in range(len(entry[:evtsize])):
#               stddev[val]+=(entry[evtsize]/sum_weights)*(averages[val]-entry[val])**2
#       return [averages,stddev]
    
    def fit(self,hitlist):
        """
        Runs the fit and returns the averaged bestfit and errors

        Args:
            hitlist (list): A list of hit layers.

        Returns:
            list: The averages and standard deviations.
        """
        lines=self.define_lines(hitlist)
        #return lines #DEBUG
        if(len(lines)==0):
            raise Exception("No valid fit found")
        bestfit = self.average_lines(lines)
        #equalbounds=self.get_equal_bounds(lines) #in development
        return bestfit 

    def get_equal_bounds(self, linelist):
        xvals=[np.inf, -np.inf]
        yvals=[np.inf, -np.inf]
        txvals=[np.inf, -np.inf]
        tyvals=[np.inf, -np.inf]

        for line in linelist:
            if(line[-1]!=1): continue
            if(line[0]<xvals[0]): xvals[0]=line[0]
            if(line[0]>xvals[1]): xvals[1]=line[0]
            if(line[1]<yvals[0]): yvals[0]=line[1]
            if(line[1]>yvals[1]): yvals[1]=line[1]
            if(line[3]<txvals[0]): txvals[0]=line[3]
            if(line[3]>txvals[1]): txvals[1]=line[3]
            if(line[4]<tyvals[0]): tyvals[0]=line[4]
            if(line[4]>tyvals[1]): tyvals[1]=line[4]
            #print(line)
            #print([xvals,yvals,txvals,tyvals])
        return [xvals,yvals,txvals,tyvals]

    def faces_from_points(self,vertices): #assumes 6 sided object
        """
        Constructs a list of faces for 3D plotting.

        Args:
            vertices (list): A list of vertices with coordinates.

        Returns:
            list: A list of faces defined by the vertices.
        """
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],  # V1
            [vertices[4], vertices[5], vertices[6], vertices[7]],  # V2
            [vertices[0], vertices[1], vertices[5], vertices[4]],  # Side 1
            [vertices[1], vertices[2], vertices[6], vertices[5]],  # Side 2
            [vertices[2], vertices[3], vertices[7], vertices[6]],  # Side 3
            [vertices[3], vertices[0], vertices[4], vertices[7]]   # Side 4
        ]
        return faces
    def get_prism(self, fit):
        """
        Constructs the 1 sigma fit prisms projecting through the hit layers

        Args:
            fit (list): fit results

        Returns:
            list: A list of faces defining the prisms.
        """
        x=fit[0][0]
        xstep=fit[1][0]
        y=fit[0][1]
        ystep=fit[1][1]
        z=fit[0][2]
        tx=fit[0][3]
        txstep=fit[1][3]
        ty=fit[0][4]
        tystep=fit[1][4]

        scale=1000

        top=np.array([
            [x-xstep,y-ystep,z], #central rectangle
            [x+xstep,y-ystep,z],
            [x+xstep,y+ystep,z],
            [x-xstep,y+ystep,z],
            [x-xstep+(scale/np.tan(tx+txstep)),y-ystep+(scale/np.tan(ty+tystep)),z+scale], #top rectangle
            [x+xstep+(scale/np.tan(tx-txstep)),y-ystep+(scale/np.tan(ty+tystep)),z+scale],
            [x+xstep+(scale/np.tan(tx-txstep)),y+ystep+(scale/np.tan(ty-tystep)),z+scale],
            [x-xstep+(scale/np.tan(tx+txstep)),y+ystep+(scale/np.tan(ty-tystep)),z+scale]
        ])
        bottom=np.array([
            [x-xstep,y-ystep,z], #central rectangle
            [x+xstep,y-ystep,z],
            [x+xstep,y+ystep,z],
            [x-xstep,y+ystep,z],
            [x-xstep-(scale/np.tan(tx-txstep)),y-ystep-(scale/np.tan(ty-tystep)),z-scale], #bottom rectangle
            [x+xstep-(scale/np.tan(tx+txstep)),y-ystep-(scale/np.tan(ty-tystep)),z-scale],
            [x+xstep-(scale/np.tan(tx+txstep)),y+ystep-(scale/np.tan(ty+tystep)),z-scale],
            [x-xstep-(scale/np.tan(tx-txstep)),y+ystep-(scale/np.tan(ty+tystep)),z-scale]
        ])
        faces=self.faces_from_points(top)
        faces=faces+self.faces_from_points(bottom)
        return faces
        
    def get_bar(self,hit):
        """
        Constructs a 3D bar representation for plotting.

        Args:
            hit (dict): A dictionary with keys 'x', 'y', and 'z' representing a hit point.

        Returns:
            list: A list of faces defining the bar.
        """
        x=hit['x']
        y=hit['y']
        z=hit['z']
        xs=0 #orientation
        ys=0
        
        if(z==0 or z==160):
            xs=5
            ys=2
        else:
            xs=2
            ys=5
        vertices=np.array([
            [x-xs,y-ys,z+0.5], #Top Face
            [x+xs,y-ys,z+0.5],
            [x+xs,y+ys,z+0.5],
            [x-xs,y+ys,z+0.5],
            [x-xs,y-ys,z-0.5], #Bottom Face
            [x+xs,y-ys,z-0.5],
            [x+xs,y+ys,z-0.5],
            [x-xs,y+ys,z-0.5]
        ])
        return self.faces_from_points(vertices)
