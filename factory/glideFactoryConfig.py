#
# Project:
#   glideinWMS
#
# File Version: 
#   $Id: glideFactoryConfig.py,v 1.25 2011/05/19 21:19:07 parag Exp $
#

import string
import os
import os.path
import sys
import time
import shutil

############################################################
#
# Configuration
#
############################################################

class FactoryConfig:
    def __init__(self):
        # set default values
        # user should modify if needed

        self.glidein_descript_file = "glidein.descript"
        self.job_descript_file = "job.descript"
        self.job_attrs_file = "attributes.cfg"
        self.job_params_file = "params.cfg"
        self.frontend_descript_file = "frontend.descript"

# global configuration of the module
factoryConfig=FactoryConfig()


############################################################
#
# Generic Class
# You most probably don't want to use these
#
############################################################

# loads a file composed of
#   NAME VAL
# and creates
#   self.data[NAME]=VAL
# It also defines:
#   self.config_file="name of file"
class ConfigFile:
    def __init__(self,config_file,convert_function=repr):
        self.config_file=config_file
        self.load(config_file,convert_function)

    def load(self,fname,convert_function):
        self.data={}
        fd=open(fname,"r")
        try:
            lines=fd.readlines()
            for line in lines:
                if line[0]=="#":
                    continue # comment
                if len(string.strip(line))==0:
                    continue # empty line
                larr=string.split(line,None,1)
                lname=larr[0]
                if len(larr)==1:
                    lval=""
                else:
                    lval=larr[1][:-1] #strip newline
                exec("self.data['%s']=%s"%(lname,convert_function(lval)))
        finally:
            fd.close()

# load from the entry subdir
class EntryConfigFile(ConfigFile):
    def __init__(self,entry_name,config_file,convert_function=repr):
        ConfigFile.__init__(self,os.path.join("entry_"+entry_name,config_file),convert_function)
        self.entry_name=entry_name
        self.config_file_short=config_file

# load both the main and entry subdir config file
# and join the results
class JoinConfigFile(ConfigFile):
    def __init__(self,entry_name,config_file,convert_function=repr):
        ConfigFile.__init__(self,config_file,convert_function)
        self.entry_name=entry_name
        entry_obj=EntryConfigFile(entry_name,config_file,convert_function)
        #merge by overriding whatever is found in the subdir
        for k in entry_obj.data.keys():
            self.data[k]=entry_obj.data[k]

############################################################
#
# Configuration
#
############################################################

class GlideinKey:
    def __init__(self,pub_key_type,key_fname=None,recreate=False):
        self.pub_key_type=pub_key_type
        self.load(key_fname,recreate)

    def load(self,key_fname=None,recreate=False):
        """
        Create the key if required and initialize it
        
        @type key_fname: String
        @param key_fname: Filename of the key
        @type recreate: bool
        @param recreate: Create a new key if True else load existing key. Defaults to False.
          
        """
        
        if self.pub_key_type=='RSA':
            import pubCrypto,symCrypto,md5
            if key_fname==None:
                key_fname='rsa.key'

            self.rsa_key=pubCrypto.RSAKey(key_fname=key_fname)

            if recreate:
                # recreate it
                self.rsa_key.new()
                self.rsa_key.save(key_fname)

            self.pub_rsa_key=self.rsa_key.PubRSAKey()
            self.pub_key_id=md5.new(string.join((self.pub_key_type,self.pub_rsa_key.get()))).hexdigest()
            self.sym_class=symCrypto.AutoSymKey
        else:
            raise RuntimeError, 'Invalid pub key type value(%s), only RSA supported'%self.pub_key_type

    def get_pub_key_type(self):
        return self.pub_key_type[0:]

    def get_pub_key_value(self):
        if self.pub_key_type=='RSA':
            return self.pub_rsa_key.get()
        else:
            raise RuntimeError, 'Invalid pub key type value(%s), only RSA supported'%self.pub_key_type

    def get_pub_key_id(self):
        return self.pub_key_id[0:]

    # extracts the symkey from encrypted fronted attribute
    # returns a SymKey child object
    def extract_sym_key(self,enc_sym_key):
        if self.pub_key_type=='RSA':
            sym_key_code=self.rsa_key.decrypt_hex(enc_sym_key)
            return self.sym_class(sym_key_code)
        else:
            raise RuntimeError, 'Invalid pub key type value(%s), only RSA supported'%self.pub_key_type        

class GlideinDescript(ConfigFile):
    def __init__(self):
        global factoryConfig
        ConfigFile.__init__(self,factoryConfig.glidein_descript_file,
                            repr) # convert everything in strings
        if self.data['PubKeyType']=='None':
            self.data['PubKeyType']=None
        self.default_rsakey_fname = 'rsa.key'
        self.backup_rsakey_fname = 'rsa.key.bak'


    def backup_and_load_old_key(self):
        """
        Backup existing key and load the key object
        """
 
        if self.data['PubKeyType'] != None:
            self.backup_rsa_key()
        self.load_old_rsa_key()
                
    def backup_rsa_key(self):
        """
        Backup existing rsa key.
        """
        
        if self.data['PubKeyType'] == 'RSA':
            try:
                shutil.copy(self.default_rsakey_fname, self.backup_rsakey_fname)
                self.data['OldPubKeyType'] = self.data['PubKeyType']
                return
            except:
                # In case of failure, the requests from frontend get
                # delayed. So it is not critical enough to fail.
                pass
            
        self.data['OldPubKeyType'] = None
        self.data['OldPubKeyObj'] = None
        return

    def load_old_rsa_key(self):
        """
        Load the old key object.
        """

        # Assume that old key if exists is of same type
        self.data['OldPubKeyType'] = self.data['PubKeyType']
        self.data['OldPubKeyObj'] = None

        if self.data['OldPubKeyType'] != None:
            try:
                self.data['OldPubKeyObj'] = GlideinKey(self.data['OldPubKeyType'],
                                                       key_fname=self.backup_rsakey_fname)
            except:
                self.data['OldPubKeyType'] = None
                self.data['OldPubKeyObj'] = None
        return

    def remove_old_key(self):
        try:
            os.remove(self.backup_rsakey_fname)
        except:
            self.data['OldPubKeyType'] = None
            self.data['OldPubKeyObj'] = None
            raise
        self.data['OldPubKeyType'] = None
        self.data['OldPubKeyObj'] = None
        return
    
    def load_pub_key(self,recreate=False):
        """
        Load the key object. Create the key if required
        
        @type recreate: bool
        @param recreate: Create a new key overwriting the old one. Defaults to False
        """
        
        if self.data['PubKeyType']!=None:
            self.data['PubKeyObj']=GlideinKey(self.data['PubKeyType'], 
                                              key_fname=self.default_rsakey_fname,
                                              recreate=recreate)
        else:
            self.data['PubKeyObj']=None
        return

class JobDescript(EntryConfigFile):
    def __init__(self,entry_name):
        global factoryConfig
        EntryConfigFile.__init__(self,entry_name,factoryConfig.job_descript_file,
                                 repr) # convert everything in strings

class JobAttributes(JoinConfigFile):
    def __init__(self,entry_name):
        global factoryConfig
        JoinConfigFile.__init__(self,entry_name,factoryConfig.job_attrs_file,
                                lambda s:s) # values are in python format

class JobParams(JoinConfigFile):
    def __init__(self,entry_name):
        global factoryConfig
        JoinConfigFile.__init__(self,entry_name,factoryConfig.job_params_file,
                                lambda s:s) # values are in python format


# Data format:
#  obj.data[frontend]['ident']=identity
#  obj.data[frontend]['usermap'][sec_class]=username
class FrontendDescript(ConfigFile):
    def __init__(self):
        global factoryConfig
        ConfigFile.__init__(self,factoryConfig.frontend_descript_file,
                            lambda s:s) # values are in python format

    # returns None if the frontend is unknown
    def get_identity(self,frontend):
        if self.data.has_key(frontend):
            fe=self.data[frontend]
            return fe['ident']
        else:
            return None

    # return None, if not found/not authorized
    def get_username(self,frontend,sec_class):
        if self.data.has_key(frontend):
            fe=self.data[frontend]['usermap']
            if fe.has_key(sec_class):
                return fe[sec_class]

        return None

    # returns a list of all the usernames assigned to the frontends
    def get_all_usernames(self):
        usernames={}
        for frontend in self.data.keys():
            fe=self.data[frontend]['usermap']
            for sec_class in fe.keys():
                username=fe[sec_class]
                usernames[username]=True
        return usernames.keys()
    
        
