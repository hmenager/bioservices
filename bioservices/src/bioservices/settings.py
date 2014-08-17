# -*- coding: utf-8 -*-
"""
Created on Fri Aug  8 15:31:34 2014

@author: cokelaer
"""
import os
from easydev import DynamicConfigParser
import sys
import tempfile
import copy
import types

__all__ = ["get_bioservices_env", "defaultParams", "BioServicesConfig"]


# first item if the value
# second item if a type or TUPLE of types possible
# third item is documentation
defaultParams = {
    'general.timeout': [3, (int,float), ""],
    'general.max_retries': [3, int, ''],
    'general.async_concurrent' : [50, int, ''], 
    'general.async_threshold': [10 , int, 'when to switch to asynchronous requests'],
    'cache.tag_suffix': ["_bioservices_database",str, 'suffix to append for cache databases'],
    'cache.on' : [False, bool, 'CACHING on/off'],
    'cache.fast': [True, bool, "FAST_CACHE option"],
    'chemspider.token': [None, (str, types.NoneType), 'token see http://www.chemspider.com'],
}


def get_bioservices_env(section, option):
    bs = BioServicesConfig()

    # Create the configuration from scratch
    if os.path.isfile(bs.config_file) == False:
        bs.cf.add_section("chemspider")
        bs.cf.set("chemspider", "token", "")
        fh = open(bs.config_file, "w")
        bs.cf.write(fh)
        fh.close()
        raise ValueError("""No token found for chemspider. 
        Creating one on http//www.chemspider.com and provide it when creating instance of ChemSpider""")
    else:
        bs.cf.read(bs.config_file)
        value = bs.cf.get(section, option)
        if value=="":
            raise ValueError("""No token found for chemspider. 
            Creating one on http//www.chemspider.com and provide it when creating instance of ChemSpider""")
        return value



class Params(dict):
    def __init__(self):
        pass

import appdirs

class ConfigReadOnly(object):
    """A generic Config file handler
    
    Uses appdirs from ypi to handle the XDG protocol

    Read the configuration in the XDG directory. If not found, the
    config and cache directories are created. Then, reads the configuration
    file. If not found, nothing happens. A dictionary should be provided
    to initialise the default parameters. This dictionary is updated
    wit the content of the user config file if any. Reset the parameters
    to the default values is possible at any time. Re-read the user
    config file is possible at any time (meth:`read_`)

    """
    def __init__(self, name=None, default_params={}):
        """name is going to be the generic name of the config folder
        
        e.g., /home/user/.config/<name>/<name>.cfg

        """
        if name == None:
            raise Exception("Name parameter must be provided")
        else:
            # use input parameters
            self.name = name
            self._default_params = copy.deepcopy(default_params)
            self.params = copy.deepcopy(default_params)

            # usefule tool to handle XDG config file, path and parameters
            self.appdirs = appdirs.AppDirs(self.name)
            self.config_parser = DynamicConfigParser()
            # Now, create the missing directories if needed
            self.init() # and read the user config file updating params if needed
            
    def read_user_config_file_and_update_params(self):
        """Read the configuration file and update parameters

        Read the configuration file (file with extension cfg and name of your
        app). Section and option found will be used to update the :attr:`params`.

        If a set of section/option is not correct (not in the :attr:`params`) then
        it is ignored.

        The :attr:`params` is a dictionary with keys being labelled as <section>.<option>
        For instance, the key "cache.on" should be written in the configuration file as::

            [cache]
            on = True

        where True is the expected value.

        
        """
        self.config_parser.read(self.user_config_file_path)
        for section in self.config_parser.sections():
            dic = self.config_parser.section2dict(section)
            for key in dic.keys():
                value = dic[key]
                newkey = section + '.' + key
                if newkey in self.params.keys():
                    # the type should be self.params[newkey][1]
                    cast = self.params[newkey][1]
                    # somehow 
                    if isinstance(value, cast) == True:
                        self.params[newkey][0] = value
                    else:
                        print("Warning:: found an incorrect type while parsing {} file. In section '{}', the option '{}' should be a {}. Found value {}. Trying a cast...".format(self.user_config_file_path, section, key, cast, value))
                        self.params[newkey][0] = cast(value)
                else:
                    print("Warning:: found invalid option or section in %s (ignored):" % self.user_config_file_path)
                    print("   %s %s" % (section, option))

    def _get_home(self):    
        # This function should be robust   
        # First, let us try with expanduser
        try:
            homedir = os.path.expanduser("~")
        except ImportError:
            # This may happen.
            pass
        else:
            if os.path.isdir(homedir):
                return homedir
        # Then, with getenv
        for this in ('HOME', 'USERPROFILE', 'TMP'):
            # getenv is same as os.environ.get
            homedir = os.environ.get(this)
            if homedir is not None and os.path.isdir(homedir):
                return homedir
        return None
    home = property(_get_home)

    def _mkdirs(self, newdir, mode=0o777):
        """from matplotlib mkdirs
        
        make directory *newdir* recursively, and set *mode*.  Equivalent to ::

        > mkdir -p NEWDIR
        > chmod MODE NEWDIR
        """
        try:
            if not os.path.exists(newdir):
                parts = os.path.split(newdir)
                for i in range(1, len(parts) + 1):
                    thispart = os.path.join(*parts[:i])
                    if not os.path.exists(thispart):
                        os.makedirs(thispart, mode)

        except OSError as err:
            # Reraise the error unless it's about an already existing directory
            if err.errno != errno.EEXIST or not os.path.isdir(newdir):
                raise

    def _get_and_create(self, sdir):
        if not os.path.exists(sdir):
            print("Creating directory %s " % sdir)
            try:
                self._mkdirs(sdir)
            except:
                print("Could not create the path %s " % sdir)
                return None
        return sdir

    def _get_config_dir(self):
        sdir = self.appdirs.user_config_dir
        return self._get_and_create(sdir)
    user_config_dir = property(_get_config_dir)

    def _get_cache_dir(self):
        sdir = self.appdirs.user_cache_dir
        return self._get_and_create(sdir)
    user_cache_dir = property(_get_cache_dir)

    def _get_config_file_path(self):
        return self.user_config_dir + os.sep +self.config_file
    user_config_file_path = property(_get_config_file_path)

    def _get_config_file(self):
        return self.name + ".cfg"
    config_file = property(_get_config_file)

    def init(self):
        # Let us create the directories by simply getting these 2 attributes:
        try:
            _ = self.user_config_dir
        except:
            print("Could not retrieve or create the config file and/or directory in %s" % self.name)
        try:    
            _ = self.user_cache_dir
        except:
            print("Could not retrieve or create the cache file and/or directory in %s" % self.name)
        self.read_user_config_file_and_update_params()

    def create_default_config_file(self, force=False):

        # if the file already exists, we should save the file into
        # a backup file
        if os.path.exists(self.user_config_file_path):
            # we need to copy the file into a backup file
            filename = self.user_config_file_path + '.bk'
            if os.path.exists(filename) and force==False:
                print("""Trying to save the current config file {} into a backup file {}\n but it exists already. Please remove the backup file first or set the 'force' parameter to True""".format(self.user_config_file_path, filename))
                return
            else:
                import shutil
                shutil.copy(self.user_config_file_path, filename)

        # Now, we can rewrite the configuration file
        sections = sorted(set([x.split(".")[0] for x in self._default_params.keys()]))
        if 'general' in sections:
            sections = ["general"] + [x for x in sections if x!="general"]

        fh = open(self.user_config_file_path, "w") # open and delete content
        for section in sections:
            fh.write("[" + section +"]\n")
            options = [x.split(".")[1] for x in self._default_params.keys() if x.startswith(section+".")]
            for option in options:
                key = section + '.' + option    
                value = self._default_params[key]
                fh.write("# {}\n{} = {}\n".format(value[2], option, value[0]))
            fh.write("\n")
        fh.close()
                
    def reload_default_params(self):
        self.params = copy.deepcopy(self._default_params)



class BioServicesConfig(ConfigReadOnly):
    def __init__(self):
        super(BioServicesConfig, self).__init__(name="bioservices", 
                default_params=defaultParams)






