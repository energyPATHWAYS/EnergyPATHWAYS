# -*- coding: utf-8 -*-
"""
Created on Sat Aug 15 12:55:25 2015

@author: Ben
"""

# def write_IO(self):
# """write IO_table for all supply subsectors and solves for final demand"""
# #creates empty IO table with all subsectors
# IO_table = pd.DataFrame(0,index = self.subsectors.keys(),
# columns = self.subsectors.keys(),dtype=float)
# #writes IO table flows from database
# for column in self.subsectors.keys():
# for index in self.subsectors.keys():
# flow = util.sql_read_table('EnergyFlows', 'efficiency',subsector_ID=column, input_ID=index)
# if flow == []:
# pass
# else:
# IO_table.set_value(index,column,
#                                       util.sql_read_table('EnergyFlows', 'efficiency',
#                                                           subsector_ID=column, input_ID=index))
#        IO_array = np.matrix(IO_table.values)
#        identity_matrix = np.matrix(np.eye(len(IO_array), len(IO_array)))      
#        #creates demand dataframe and sets it from database
#        demand = pd.DataFrame(0,index=self.subsectors.keys(),columns=['value'],dtype=float)
#        for s in self.subsectors.keys():
#            demand.set_value(s,['value'],util.sql_read_table('Subsectors', 'demand',ID=s))          
#        #solves IO matrix and stores it in dataframe
#        total_demand = pd.DataFrame(np.linalg.solve(identity_matrix - IO_array, demand),
#                                          index=self.subsectors.keys(),columns=['value'])
#        #sets supply attributes of IO_table and demand                                 
#        setattr(self,'IO_table',IO_table)
#        setattr(self,'demand',total_demand)        
#    
#    def link_subsector_input_shapes(self):
#        """calculate shapes of subsector inputs and outputs"""
#        #loop through all subsectors
#        for ID in [i for i in self.subsectors.keys() if self.subsectors[i].input_shape == True]:
#            #checks if the subsector has an endogenous input shape (i.e. load)
#                #sets the initial list of subsectors to solve as ID
#                subs = [ID]
#                #while there is still a subsector to be solved that subsector has input subsectors
#                while len(subs) and len(self.subsectors[ID].input_subsectors):
#                    for ID in subs:
#                        #loop though the subsector's input_subsectors
#                        for next_ID in self.subsectors[ID].input_subsectors:
#                            if self.subsectors[next_ID].input_shape!=True:     
#                                #if the input_subsector doesn't have an endogenous input_shape then
#                                #we have to solve for the share of the active output subsector that is contributed to the input subsector shape
#                                #ex. how much of distribution delivery demand is fed by the transmission delivery subsector
#                                flow = self.subsectors[ID].input_shape_data * self.IO_table.loc[next_ID,ID]/self.IO_table[ID].sum()*self.IO_table.loc[next_ID,ID]                                              
#                                self.subsectors[next_ID].input_shape_data += flow
#                                #remove the current subsector from the input subsector's list of unsolved output_subsectors 
#                                self.subsectors[next_ID].unsolved_output_subsectors.remove(ID) 
#                            else:                                
#                                #remove the current subsector from the input subsector's list of unsolved output_subsectors 
#                                self.subsectors[next_ID].unsolved_output_subsectors.remove(ID) 
#                                #if the subsector has an endogenous input_shape then skip it                                
#                                pass
#                            continuation_subs = []
#                            #if the subsector has remaining unsolved_output_subsectors, we have to break the loop
#                            #by not adding the next_id to the continuation_subs list 
#                            if  len(self.subsectors[next_ID].unsolved_output_subsectors):                           
#                                pass
#                            else:
#                                continuation_subs.append(next_ID)
#                        #subs is replaced with the list of continuation_subs, which continues movement through the matrix
#                        subs =  continuation_subs
#            #checks if the subsector has an endogenous output shape (i.e. solar pv gen shape)
#        
#    def link_subsector_output_shapes(self):        
#        for ID in self.subsectors.keys():
#            if self.subsectors[ID].output_shape == True:  
#                #sets the initial list of subsectors to solve as ID
#                subs = [ID]
#                continuation_subs = []
#                #while there is still a subsector to be solved that has output subsectors
#                while len(subs) and len(self.subsectors[ID].output_subsectors):
#                    for ID in subs:      
#                         #loop though the subsector's output_subsectors
#                        for next_ID in self.subsectors[ID].output_subsectors:
#                            if self.subsectors[next_ID].output_shape!=True:
#                                 #if the output_subsector doesn't have an endogenous output_shape then
#                                #we have to solve for the share of the active input subsector that is contributed to the output subsector shape
#                                #ex. how much of transmission delivery supply is fed to the distribution delivery subsector
#                                output_share =(self.subsectors[ID].output_shape_data/self.subsectors[ID].output_shape_data.sum())
#                                output_share.fillna(0,inplace=True)
#                                flow = (self.subsectors[next_ID].demand * self.IO_table.loc[ID,next_ID]
#                                * output_share)
#                                self.subsectors[next_ID].output_shape_data += flow
#                                #remove the current input subsector from the output subsector's list of unsolved input_subsectors 
#                                self.subsectors[next_ID].unsolved_input_subsectors.remove(ID) 
#                            else:
#                                #remove the current input subsector from the output subsector's list of unsolved input_subsectors   
#                                self.subsectors[next_ID].unsolved_input_subsectors.remove(ID)
#                                #if the subsector has an endogenous output_shape then skip it 
#                                pass
#                            #if the subsector has remaining unsolved_input_subsectors, we have to break the loop
#                            #by not adding the next_id to the continuation_subs list 
#                            if  len(self.subsectors[next_ID].unsolved_input_subsectors):                           
#                                pass
#                            else:
#                                continuation_subs.append(next_ID)
#                        subs = continuation_subs
#            
#
#    def add_subsector_shapes(self):
#        for ID in self.subsectors.keys():
#            self.add_subsector_shape(ID)
#
#    def add_subsector_shape(self,ID):
#          subsector = self.subsectors[ID]
#          #creates default blank and flat shapes
#          blank_shape= pd.DataFrame(0,np.arange(1,25,1),
#                                  columns = ['value'])   
#          flat_shape= pd.DataFrame(1/24.0,np.arange(1,25,1),
#                                  columns = ['value'],dtype=float)
#          #determines demand of subsector
#          demand = self.demand.loc[ID,'value']
#          subsector.demand = demand
#          #if the subsector has a specified shape, shape is taken drom database 
#          if ID in util.sql_read_table('SubsectorShapes','ID'):
#              shape = pd.DataFrame(util.sql_read_table('SubsectorShapes','value',ID=ID),
#                                      index = util.sql_read_table('SubsectorShapes','time',ID=ID),
#                                      columns = ['value']) 
#              #creates uni-directional input or demand shape for consumption subsectors
#              if subsector.type=='Consumption':
#                  subsector.input_shape_data = shape.copy() * demand
#                  subsector.input_shape = True
#                  subsector.output_shape_data = blank_shape.copy()
#              #creates bi-directional input/output shapes for all other subsectors
#              else:
#                  subsector.input_shape_data = shape.copy() * demand
#                  subsector.output_shape_data = shape.copy() * demand
#                  subsector.input_shape = True
#                  subsector.output_shape = True
#          #if subsector is linked to a dispatch, it must have a base shape for calculating its 
#          #input/output signal before it has been dispatched. In this case, it can be either
#          #flat (i.e. hydro dispatch), none (i.e. thermal dispatch), or exogenous (i.e. load dispatch)
#          elif ID in util.sql_read_table('DispatchSubsectors','subsector_ID'):
#              shape_type = util.sql_read_table('DispatchSubsectors','base_shape',subsector_ID=ID)
#              if shape_type == 'exogenous':
#                  shape = pd.DataFrame(util.sql_read_table('SubsectorShapes','value',ID=ID),
#                                      index = util.sql_read_table('SubsectorShapes','time',ID=ID),
#                                      columns = ['value'])    
#              elif shape_type == 'flat':
#                  shape = flat_shape.copy()
#              else:
#                  shape = blank_shape.copy()
#              if subsector.type=='Consumption':
#                  subsector.input_shape_data= shape.copy()*demand
#                  subsector.input_shape = True
#                  subsector.output_shape_data = blank_shape.copy()
#              else:
#                  subsector.input_shape_data = shape.copy() * demand
#                  subsector.output_shape_data = shape.copy() * demand
#                  subsector.input_shape = True
#                  subsector.output_shape = True              
#          else:
#              if subsector.type=='Consumption':
#                  subsector.input_shape_data,subsector.output_shape_data = flat_shape.copy()*demand,blank_shape.copy()*demand
#                  subsector.input_shape=True
#              else:    
#                  subsector.input_shape_data,subsector.output_shape_data = blank_shape.copy(), blank_shape.copy()
#    def add_subsectors_io(self):
#        for ID in self.subsectors.keys():
#            self.add_subsector_io(ID)
#    def add_subsector_io(self,ID):
#          for sub in self.subsectors.keys():
#             if self.IO_table.loc[ID,sub]!= 0:
#                  self.subsectors[ID].output_subsectors.append(sub)
#                  self.subsectors[ID].unsolved_output_subsectors.append(sub)
#             elif self.IO_table.loc[sub,ID]!=0:
#                  self.subsectors[ID].input_subsectors.append(sub)
#                  self.subsectors[ID].unsolved_input_subsectors.append(sub)   