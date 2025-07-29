# -*- coding: utf-8 -*-

import cohesity_management_sdk.models_v2.key_value_pair
import cohesity_management_sdk.models_v2.redo_log_config
import cohesity_management_sdk.models_v2.oracle_update_restore_options
import cohesity_management_sdk.models_v2.oracle_protection_group_database_node_channel
import cohesity_management_sdk.models_v2.shell_key_value_pair
import cohesity_management_sdk.models_v2.recover_oracle_granular_restore_information

class RecoverDatabaseParams(object):

    """Implementation of the 'RecoverDatabaseParams' model.

    Specifies recovery parameters when recovering to a database

    Attributes:
        database_name (string): Specifies a new name for the restored
            database. If this field is not specified, then the original
            database will be overwritten after recovery.
        oracle_base_folder (string): Specifies the oracle base folder at
            selected host.
        oracle_home_folder (string): Specifies the oracle home folder at
            selected host.
        db_files_destination (string): Specifies the location to restore
            database files.
        db_config_file_path (string): Specifies the config file path on
            selected host which configures the restored database.
        enable_archive_log_mode (bool): Specifies archive log mode for oracle
            restore.
        pfile_parameter_map (list of KeyValuePair): Specifies a key value pair
            for pfile parameters.
        bct_file_path (string): Specifies BCT file path.
        num_tempfiles (int): Specifies no. of tempfiles to be used for the
            recovered database.
        redo_log_config (RedoLogConfig): Specifies redo log config.
        is_multi_stage_restore (bool): Specifies whether this task is a
            multistage restore task. If set, we migrate the DB after clone
            completes.
        oracle_update_restore_options (OracleUpdateRestoreOptions): Specifies
            the parameters that are needed for updating oracle restore
            options.
        restore_time_usecs (long|int): Specifies the time in the past to which
            the Oracle db needs to be restored. This allows for granular
            recovery of Oracle databases. If this is not set, the Oracle db
            will be restored from the full/incremental snapshot.
        db_channels (list of OracleProtectionGroupDatabaseNodeChannel):
            Specifies the Oracle database node channels info. If not
            specified, the default values assigned by the server are applied
            to all the databases.
        recovery_mode (bool): Specifies if database should be left in recovery
            mode.
        shell_evironment_vars (list of ShellKeyValuePair): Specifies key value
            pairs of shell variables which defines the restore shell
            environment.
        granular_restore_info (RecoverOracleGranularRestoreInformation):
            Specifies information about list of objects (PDBs) to restore.

    """

    # Create a mapping from Model property names to API property names
    _names = {
        "database_name":'databaseName',
        "oracle_base_folder":'oracleBaseFolder',
        "oracle_home_folder":'oracleHomeFolder',
        "db_files_destination":'dbFilesDestination',
        "db_config_file_path":'dbConfigFilePath',
        "enable_archive_log_mode":'enableArchiveLogMode',
        "pfile_parameter_map":'pfileParameterMap',
        "bct_file_path":'bctFilePath',
        "num_tempfiles":'numTempfiles',
        "redo_log_config":'redoLogConfig',
        "is_multi_stage_restore":'isMultiStageRestore',
        "oracle_update_restore_options":'oracleUpdateRestoreOptions',
        "restore_time_usecs":'restoreTimeUsecs',
        "db_channels":'dbChannels',
        "recovery_mode":'recoveryMode',
        "shell_evironment_vars":'shellEvironmentVars',
        "granular_restore_info":'granularRestoreInfo'
    }

    def __init__(self,
                 database_name=None,
                 oracle_base_folder=None,
                 oracle_home_folder=None,
                 db_files_destination=None,
                 db_config_file_path=None,
                 enable_archive_log_mode=None,
                 pfile_parameter_map=None,
                 bct_file_path=None,
                 num_tempfiles=None,
                 redo_log_config=None,
                 is_multi_stage_restore=None,
                 oracle_update_restore_options=None,
                 restore_time_usecs=None,
                 db_channels=None,
                 recovery_mode=None,
                 shell_evironment_vars=None,
                 granular_restore_info=None):
        """Constructor for the RecoverDatabaseParams class"""

        # Initialize members of the class
        self.database_name = database_name
        self.oracle_base_folder = oracle_base_folder
        self.oracle_home_folder = oracle_home_folder
        self.db_files_destination = db_files_destination
        self.db_config_file_path = db_config_file_path
        self.enable_archive_log_mode = enable_archive_log_mode
        self.pfile_parameter_map = pfile_parameter_map
        self.bct_file_path = bct_file_path
        self.num_tempfiles = num_tempfiles
        self.redo_log_config = redo_log_config
        self.is_multi_stage_restore = is_multi_stage_restore
        self.oracle_update_restore_options = oracle_update_restore_options
        self.restore_time_usecs = restore_time_usecs
        self.db_channels = db_channels
        self.recovery_mode = recovery_mode
        self.shell_evironment_vars = shell_evironment_vars
        self.granular_restore_info = granular_restore_info


    @classmethod
    def from_dictionary(cls,
                        dictionary):
        """Creates an instance of this model from a dictionary

        Args:
            dictionary (dictionary): A dictionary representation of the object as
            obtained from the deserialization of the server's response. The keys
            MUST match property names in the API description.

        Returns:
            object: An instance of this structure class.

        """
        if dictionary is None:
            return None

        # Extract variables from the dictionary
        database_name = dictionary.get('databaseName')
        oracle_base_folder = dictionary.get('oracleBaseFolder')
        oracle_home_folder = dictionary.get('oracleHomeFolder')
        db_files_destination = dictionary.get('dbFilesDestination')
        db_config_file_path = dictionary.get('dbConfigFilePath')
        enable_archive_log_mode = dictionary.get('enableArchiveLogMode')
        pfile_parameter_map = None
        if dictionary.get("pfileParameterMap") is not None:
            pfile_parameter_map = list()
            for structure in dictionary.get('pfileParameterMap'):
                pfile_parameter_map.append(cohesity_management_sdk.models_v2.key_value_pair.KeyValuePair.from_dictionary(structure))
        bct_file_path = dictionary.get('bctFilePath')
        num_tempfiles = dictionary.get('numTempfiles')
        redo_log_config = cohesity_management_sdk.models_v2.redo_log_config.RedoLogConfig.from_dictionary(dictionary.get('redoLogConfig')) if dictionary.get('redoLogConfig') else None
        is_multi_stage_restore = dictionary.get('isMultiStageRestore')
        oracle_update_restore_options = cohesity_management_sdk.models_v2.oracle_update_restore_options.OracleUpdateRestoreOptions.from_dictionary(dictionary.get('oracleUpdateRestoreOptions')) if dictionary.get('oracleUpdateRestoreOptions') else None
        restore_time_usecs = dictionary.get('restoreTimeUsecs')
        db_channels = None
        if dictionary.get("dbChannels") is not None:
            db_channels = list()
            for structure in dictionary.get('dbChannels'):
                db_channels.append(cohesity_management_sdk.models_v2.oracle_protection_group_database_node_channel.OracleProtectionGroupDatabaseNodeChannel.from_dictionary(structure))
        recovery_mode = dictionary.get('recoveryMode')
        shell_evironment_vars = None
        if dictionary.get("shellEvironmentVars") is not None:
            shell_evironment_vars = list()
            for structure in dictionary.get('shellEvironmentVars'):
                shell_evironment_vars.append(cohesity_management_sdk.models_v2.shell_key_value_pair.ShellKeyValuePair.from_dictionary(structure))
        granular_restore_info = cohesity_management_sdk.models_v2.recover_oracle_granular_restore_information.RecoverOracleGranularRestoreInformation.from_dictionary(dictionary.get('granularRestoreInfo')) if dictionary.get('granularRestoreInfo') else None

        # Return an object of this model
        return cls(database_name,
                   oracle_base_folder,
                   oracle_home_folder,
                   db_files_destination,
                   db_config_file_path,
                   enable_archive_log_mode,
                   pfile_parameter_map,
                   bct_file_path,
                   num_tempfiles,
                   redo_log_config,
                   is_multi_stage_restore,
                   oracle_update_restore_options,
                   restore_time_usecs,
                   db_channels,
                   recovery_mode,
                   shell_evironment_vars,
                   granular_restore_info)


