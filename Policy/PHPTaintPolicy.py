"""
Credits to:
RIPS - A static source code analyser for vulnerabilities in PHP scripts 
by Johans Dahse (johannes.dahse@rub.de)

"""

class TaintPolicy:
    #Types of attacks
    NAME_XSS = 'Cross-Site Scripting'
    NAME_POP = 'PHP Object Injection'
    NAME_HTTP_HEADER = 'HTTP Response Splitting'
    NAME_SSRF = 'Server-Side Request Forgery'
    NAME_SESSION_FIXATION = 'Session Fixation'
    NAME_CODE = 'Code Execution'
    NAME_REFLECTION = 'Reflection Injection'
    NAME_OTHER = 'Possible Flow Control' # :X
    NAME_CONNECT = 'Protocol Injection'
    NAME_LDAP = 'LDAP Injection'
    NAME_XPATH = 'XPath Injection'
    NAME_DATABASE = 'SQL Injection'
    NAME_FILE_READ = 'File Disclosure'
    NAME_FILE_INCLUDE = 'File Inclusion'
    NAME_FILE_AFFECT = 'File Manipulation'
    NAME_EXEC = 'Command Execution'

    def __init__(self):
        self.sanitizer = self.Sanitizer()
        self.sink = self.Sink()
        self.source = self.Source()

        # 0 means all parameter.
        # i.e if any of the input of array_push is tainted, the output of array_push will be tainted (which is the var in parameter 1).
        self.propagator = {
        'array_push' : [[1],[0]]
        }

    class Sanitizer:
        FUNC_LIST = [ "F_SECURING_STRING"]
        F_SECURING_LDAP = []
        F_SECURING_XPATH = [
        'addslashes'
        ]
        F_SECURING_FILE = [
        'basename',
        'dirname',
        'pathinfo'
        ]
        CONDITIONAL_FUNC_LIST = [ 
        "F_SECURING_XSS",
        "F_SECURING_PREG",
        "F_SECURING_SYSTEM",
        "F_SECURING_SQL"
        ]
        F_SECURING_XSS = [
        'htmlentities', 
        'htmlspecialchars',
        'highlight_string',
        # Wordpress
        'esc_attr',
        'esc_html'
        ]

        F_SECURING_SQL = [
        'addslashes',
        'dbx_escape_string',
        'db2_escape_string',
        'ingres_escape_string',
        'maxdb_escape_string',
        'maxdb_real_escape_string',
        'mysql_escape_string',
        'mysql_real_escape_string',
        'mysqli_escape_string',
        'mysqli_real_escape_string',
        'pg_escape_string', 
        'pg_escape_bytea',
        'sqlite_escape_string',
        'sqlite_udf_encode_binary',
        'cubrid_real_escape_string'
        ]  

        F_SECURING_PREG = [
        'preg_quote'
        ]

        F_SECURING_SYSTEM = [
        'escapeshellarg',
        'escapeshellcmd'
        ]

        #securing functions for every vulnerability
        F_SECURING_STRING = [
        'Expr_Cast_Bool',
        'Expr_Cast_Int',
        'Expr_Cast_Double',
        'Expr_Cast_Unset',
        'intval',
        'floatval',
        'doubleval',
        'filter_input',
        'urlencode',
        'rawurlencode',
        'round',
        'floor',
        'strlen',
        'strrpos',
        'strpos',
        'strftime',
        'strtotime',
        'md5',
        'md5_file',
        'sha1',
        'sha1_file',
        'crypt',
        'crc32',
        'hash',
        'mhash',
        'hash_hmac',
        'password_hash',
        'mcrypt_encrypt',
        'mcrypt_generic',
        'base64_encode',
        'ord',
        'sizeof',
        'count',
        'bin2hex',
        'levenshtein',
        'abs',
        'bindec',
        'decbin',
        'dechex',
        'decoct',
        'hexdec',
        'rand',
        'max',
        'min',
        'metaphone',
        'tempnam',
        'soundex',
        'money_format',
        'number_format',
        'date_format',
        'filetype',
        'nl_langinfo',
        'bzcompress',
        'convert_uuencode',
        'gzdeflate',
        'gzencode',
        'gzcompress',
        'http_build_query',
        'lzf_compress',
        'zlib_encode',
        'imap_binary',
        'iconv_mime_encode',
        'bson_encode',
        'sqlite_udf_encode_binary',
        'session_name',
        'readlink',
        'getservbyport',
        'getprotobynumber',
        'gethostname',
        'gethostbynamel',
        'gethostbyname',
        ]

    class Sink:
        FUNC_LIST = ["F_XSS","F_CODE","F_EXEC","F_DATABASE","F_SSRF","F_HTTP_HEADER","F_POP","F_OTHER","F_CONNECT","F_SESSION_FIXATION","F_REFLECTION","F_FILE_READ","F_FILE_AFFECT","F_LDAP","F_XPATH","F_FILE_INCLUDE"]
        # cross-site scripting affected functions
        # parameter = 0 means, all parameters will be traced
        def __init__(self):

            self.F_FILE_INCLUDE = {
            'include'                       : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'include_once'                  : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'parsekit_compile_file'         : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'php_check_syntax'              : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],   
            'require'                       : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'require_once'                  : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'runkit_import'                 : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'set_include_path'              : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'virtual'                       : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE]
            }

            self.F_XPATH = {
            'xpath_eval'                    : [[2], TaintPolicy.Sanitizer().F_SECURING_XPATH],  
            'xpath_eval_expression'         : [[2], TaintPolicy.Sanitizer().F_SECURING_XPATH],      
            'xptr_eval'                     : [[2], TaintPolicy.Sanitizer().F_SECURING_XPATH]
            }
            self.F_LDAP = {
            'ldap_add'                      : [[2,3], TaintPolicy.Sanitizer().F_SECURING_LDAP],
            'ldap_delete'                   : [[2], TaintPolicy.Sanitizer().F_SECURING_LDAP],
            'ldap_list'                     : [[3], TaintPolicy.Sanitizer().F_SECURING_LDAP],
            'ldap_read'                     : [[3], TaintPolicy.Sanitizer().F_SECURING_LDAP],
            'ldap_search'                   : [[3], TaintPolicy.Sanitizer().F_SECURING_LDAP]
            }  
            self.F_FILE_AFFECT = {
            'bzwrite'                       : [[2], []],
            'chmod'                         : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'chgrp'                         : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'chown'                         : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'copy'                          : [[1], []],
            'dio_write'                     : [[1,2], []],  
            'eio_chmod'                     : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'eio_chown'                     : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'eio_mkdir'                     : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'eio_mknod'                     : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'eio_rmdir'                     : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'eio_write'                     : [[1,2], []],
            'eio_unlink'                    : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'error_log'                     : [[3], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'event_buffer_write'            : [[2], []],
            'file_put_contents'             : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'fputcsv'                       : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'fputs'                         : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'fprintf'                       : [[0], []],    
            'ftruncate'                     : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'fwrite'                        : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE],     
            'gzwrite'                       : [[1,2], []],
            'gzputs'                        : [[1,2], []],
            'loadXML'                       : [[1], []],
            'mkdir'                         : [[1], []],
            'move_uploaded_file'            : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'posix_mknod'                   : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'recode_file'                   : [[2,3], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'rename'                        : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'rmdir'                         : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],   
            'shmop_write'                   : [[2], []],
            'touch'                         : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'unlink'                        : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'vfprintf'                      : [[0], []],    
            'xdiff_file_bdiff'              : [[3], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_bpatch'             : [[3], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_diff_binary'        : [[3], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_diff'               : [[3], TaintPolicy.Sanitizer().F_SECURING_FILE],   
            'xdiff_file_merge3'             : [[4], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_patch_binary'       : [[3], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_patch'              : [[3], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_rabdiff'            : [[3], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'yaml_emit_file'                : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE],
            }
            self.F_FILE_READ = {
            'bzread'                        : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'bzflush'                       : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'dio_read'                      : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],   
            'eio_readdir'                   : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],  
            'fdf_open'                      : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'file'                          : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'file_get_contents'             : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],  
            'finfo_file'                    : [[1,2], []], 
            'fflush'                        : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'fgetc'                         : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'fgetcsv'                       : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'fgets'                         : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'fgetss'                        : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'fread'                         : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'fpassthru'                     : [[1,2], []], 
            'fscanf'                        : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'ftok'                          : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'get_meta_tags'                 : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'glob'                          : [[1], []], 
            'gzfile'                        : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'gzgetc'                        : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'gzgets'                        : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'gzgetss'                       : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'gzread'                        : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],  
            'gzpassthru'                    : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'highlight_file'                : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],  
            'imagecreatefrompng'            : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'imagecreatefromjpg'            : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'imagecreatefromgif'            : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'imagecreatefromgd2'            : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'imagecreatefromgd2part'        : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'imagecreatefromgd'             : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],  
            'opendir'                       : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],  
            'parse_ini_file'                : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],   
            'php_strip_whitespace'          : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],   
            'readfile'                      : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'readgzfile'                    : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE], 
            'readlink'                      : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],       
            'stat'                        : [[1], []],
            'scandir'                       : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'show_source'                   : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'simplexml_load_file'           : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'stream_get_contents'           : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'stream_get_line'               : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_bdiff'              : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_bpatch'             : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_diff_binary'        : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_diff'               : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_merge3'             : [[1,2,3], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_patch_binary'       : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_patch'              : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'xdiff_file_rabdiff'            : [[1,2], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'yaml_parse_file'               : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'zip_open'                      : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE]
            }
            self.F_FILE_INCLUDE = {
            'include'                       : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'include_once'                  : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'parsekit_compile_file'         : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'php_check_syntax'              : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],   
            'require'                       : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'require_once'                  : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'runkit_import'                 : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'set_include_path'              : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE],
            'virtual'                       : [[1], TaintPolicy.Sanitizer().F_SECURING_FILE]
            }

            self.F_REFLECTION = {
            'event_buffer_new'              : [[2,3,4], []],        
            'event_set'                     : [[4], []],
            'iterator_apply'                : [[2], []],
            'forward_static_call'           : [[1], []],
            'forward_static_call_array'     : [[1], []],
            'call_user_func'                : [[1], []],
            'call_user_func_array'          : [[1], []],        
            'array_diff_uassoc'             : [[3], []],
            'array_diff_ukey'               : [[3], []],
            'array_filter'                  : [[2], []],
            'array_intersect_uassoc'        : [[3], []],
            'array_intersect_ukey'          : [[3], []],
            'array_map'                     : [[1], []],
            'array_reduce'                  : [[2], []],
            'array_udiff'                   : [[3], []],
            'array_udiff_assoc'             : [[3], []],
            'array_udiff_uassoc'            : [[3,4], []],
            'array_uintersect'              : [[3], []],
            'array_uintersect_assoc'        : [[3], []],
            'array_uintersect_uassoc'       : [[3,4], []],      
            'array_walk'                    : [[2], []],
            'array_walk_recursive'          : [[2], []],
            'assert_options'                : [[2], []],
            'ob_start'                      : [[1], []],
            'register_shutdown_function'    : [[1], []],
            'register_tick_function'        : [[1], []],
            'runkit_method_add'             : [[1,2,3,4], []],
            'runkit_method_copy'            : [[1,2,3], []],
            'runkit_method_redefine'        : [[1,2,3,4], []],  
            'runkit_method_rename'          : [[1,2,3], []],
            'runkit_function_add'           : [[1,2,3], []],
            'runkit_function_copy'          : [[1,2], []],
            'runkit_function_redefine'      : [[1,2,3], []],
            'runkit_function_rename'        : [[1,2], []],
            'session_set_save_handler'      : [[1,2,3,4,5], []],
            'set_error_handler'             : [[1], []],
            'set_exception_handler'         : [[1], []],
            'spl_autoload'                  : [[1], []],    
            'spl_autoload_register'         : [[1], []],
            'sqlite_create_aggregate'       : [[2,3,4], []], 
            'sqlite_create_function'        : [[2,3], []], 
            'stream_wrapper_register'       : [[2], []], 
            'uasort'                        : [[2], []],
            'uksort'                        : [[2], []],
            'usort'                         : [[2], []],
            'yaml_parse'                    : [[4], []],
            'yaml_parse_file'               : [[4], []],
            'yaml_parse_url'                : [[4], []],
            'eio_busy'                      : [[3], []],
            'eio_chmod'                     : [[4], []],
            'eio_chown'                     : [[5], []],
            'eio_close'                     : [[3], []],
            'eio_custom'                    : [[1,2], []],
            'eio_dup2'                      : [[4], []],
            'eio_fallocate'                 : [[6], []],
            'eio_fchmod'                    : [[4], []],
            'eio_fchown'                    : [[5], []],
            'eio_fdatasync'                 : [[3], []],
            'eio_fstat'                     : [[3], []],
            'eio_fstatvfs'                  : [[3], []],
            'preg_replace_callback'         : [[2], []],
            'dotnet_load'                   : [[1], []],
            }

            self.F_SESSION_FIXATION = {
            'setcookie'                     : [[2], []],
            'setrawcookie'                  : [[2], []],
            'session_id'                    : [[1], []]
            }

            self.F_DATABASE = {
            # Abstraction Layers
            'dba_open'                      : [[1], []],
            'dba_popen'                     : [[1], []], 
            'dba_insert'                    : [[1,2], []],
            'dba_fetch'                     : [[1], []], 
            'dba_delete'                    : [[1], []], 
            'dbx_query'                     : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL], 
            'odbc_do'                       : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'odbc_exec'                     : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'odbc_execute'                  : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            # Vendor Specific  
            'db2_exec'                      : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'db2_execute'                   : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'fbsql_db_query'                : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'fbsql_query'                   : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL], 
            'ibase_query'                   : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL], 
            'ibase_execute'                 : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL], 
            'ifx_query'                     : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL], 
            'ifx_do'                        : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'ingres_query'                  : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'ingres_execute'                : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'ingres_unbuffered_query'       : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'msql_db_query'                 : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL], 
            'msql_query'                    : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'msql'                          : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL], 
            'mssql_query'                   : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL], 
            'mssql_execute'                 : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'mysql_db_query'                : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],  
            'mysql_query'                   : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL], 
            'mysql_unbuffered_query'        : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL], 
            'mysqli_stmt_execute'           : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'mysqli_query'                  : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'mysqli_real_query'             : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'mysqli_master_query'           : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'oci_execute'                   : [[1], []],
            'ociexecute'                    : [[1], []],
            'ovrimos_exec'                  : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'ovrimos_execute'               : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'ora_do'                        : [[2], []], 
            'ora_exec'                      : [[1], []], 
            'pg_query'                      : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'pg_send_query'                 : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'pg_send_query_params'          : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'pg_send_prepare'               : [[3], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'pg_prepare'                    : [[3], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'sqlite_open'                   : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'sqlite_popen'                  : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'sqlite_array_query'            : [[1,2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'arrayQuery'                    : [[1,2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'singleQuery'                   : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'sqlite_query'                  : [[1,2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'sqlite_exec'                   : [[1,2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'sqlite_single_query'           : [[2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'sqlite_unbuffered_query'       : [[1,2], TaintPolicy.Sanitizer().F_SECURING_SQL],
            'sybase_query'                  : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL], 
            'sybase_unbuffered_query'       : [[1], TaintPolicy.Sanitizer().F_SECURING_SQL]
            }

            self.F_CONNECT = {
            'curl_setopt'                   : [[2,3], []],
            'curl_setopt_array'             : [[2], []],
            'cyrus_query'                   : [[2], []],
            'error_log'                     : [[3], []],
            'fsockopen'                     : [[1], []], 
            'ftp_chmod'                     : [[2,3], []],
            'ftp_exec'                      : [[2], []], 
            'ftp_delete'                    : [[2], []], 
            'ftp_fget'                      : [[3], []], 
            'ftp_get'                       : [[2,3], []], 
            'ftp_nlist'                     : [[2], []], 
            'ftp_nb_fget'                   : [[3], []], 
            'ftp_nb_get'                    : [[2,3], []], 
            'ftp_nb_put'                    : [[2], []], 
            'ftp_put'                       : [[2,3], []], 
            'get_headers'                   : [[1], []],
            'imap_open'                     : [[1], []],  
            'imap_mail'                     : [[1], []],
            'mail'                          : [[1,4], []], 
            'mb_send_mail'                  : [[1,4], []], 
            'ldap_connect'                  : [[1], []],
            'msession_connect'              : [[1], []],
            'pfsockopen'                    : [[1], []],   
            'session_register'              : [[0], []],  
            'socket_bind'                   : [[2], []],  
            'socket_connect'                : [[2], []],  
            'socket_send'                   : [[2], []], 
            'socket_write'                  : [[2], []],  
            'stream_socket_client'          : [[1], []],  
            'stream_socket_server'          : [[1], []],
            'printer_open'                  : [[1], []],
            }

            self.F_OTHER = {
            'dl'                            : [[1], []],    
            'ereg'                          : [[2], []], # nullbyte injection affected      
            'eregi'                         : [[2], []], # nullbyte injection affected          
            'ini_set'                       : [[1,2], []],
            'ini_restore'                   : [[1], []],
            'runkit_constant_redefine'      : [[1,2], []],
            'runkit_method_rename'          : [[1,2,3], []],
            'sleep'                         : [[1], []],
            'usleep'                        : [[1], []],
            'extract'                       : [[1], []],
            'mb_parse_str'                  : [[1], []],
            'parse_str'                     : [[1], []],
            'putenv'                        : [[1], []],
            'set_include_path'              : [[1], []],
            'apache_setenv'                 : [[1,2], []],  
            'define'                        : [[1], []],
            'is_a'                          : [[1], []],  #calls __autoload()
            }

            self.F_POP = {
            'unserialize'                   : [[1], []], # calls gadgets
            'yaml_parse'                    : [[1], []],  # calls unserialize
            }

            self.F_SSRF = {
            'get_headers':[[0], []],
            }

            # HTTP header injections
            self.F_HTTP_HEADER = {
            'header': [[1], []],
            }

            self.F_XSS = {
            'echo': [[0], TaintPolicy.Sanitizer().F_SECURING_XSS], 
            'print': [[1], TaintPolicy.Sanitizer().F_SECURING_XSS],
            'print_r': [[1], TaintPolicy.Sanitizer().F_SECURING_XSS],
            'exit': [[1], TaintPolicy.Sanitizer().F_SECURING_XSS],
            'die': [[1], TaintPolicy.Sanitizer().F_SECURING_XSS],
            'printf': [[0], TaintPolicy.Sanitizer().F_SECURING_XSS],
            'vprintf': [[0], TaintPolicy.Sanitizer().F_SECURING_XSS],
            'trigger_error': [[1], TaintPolicy.Sanitizer().F_SECURING_XSS],
            'user_error': [[1], TaintPolicy.Sanitizer().F_SECURING_XSS],
            'odbc_result_all': [[2], TaintPolicy.Sanitizer().F_SECURING_XSS],
            'ovrimos_result_all': [[2], TaintPolicy.Sanitizer().F_SECURING_XSS],
            'ifx_htmltbl_result': [[2], TaintPolicy.Sanitizer().F_SECURING_XSS]
            }
            self.F_CODE = {
            'assert'                        : [[1], []],
            'create_function'               : [[1,2], []],
            'eval'                          : [[1], []],
            'mb_ereg_replace'               : [[1,2], TaintPolicy.Sanitizer().F_SECURING_PREG],
            'mb_eregi_replace'              : [[1,2], TaintPolicy.Sanitizer().F_SECURING_PREG],
            'preg_filter'                   : [[1,2], TaintPolicy.Sanitizer().F_SECURING_PREG],
            'preg_replace'                  : [[1,2], TaintPolicy.Sanitizer().F_SECURING_PREG],
            'preg_replace_callback'         : [[1], TaintPolicy.Sanitizer().F_SECURING_PREG],
            }

            self.F_EXEC = {
            'backticks'                     : [[1], TaintPolicy.Sanitizer().F_SECURING_SYSTEM],
            'exec'                          : [[1], TaintPolicy.Sanitizer().F_SECURING_SYSTEM],
            'expect_popen'                  : [[1], TaintPolicy.Sanitizer().F_SECURING_SYSTEM],
            'passthru'                      : [[1], TaintPolicy.Sanitizer().F_SECURING_SYSTEM],
            'pcntl_exec'                    : [[1], TaintPolicy.Sanitizer().F_SECURING_SYSTEM],
            'popen'                         : [[1], TaintPolicy.Sanitizer().F_SECURING_SYSTEM],
            'proc_open'                     : [[1], TaintPolicy.Sanitizer().F_SECURING_SYSTEM],
            'shell_exec'                    : [[1], TaintPolicy.Sanitizer().F_SECURING_SYSTEM],
            'system'                        : [[1], TaintPolicy.Sanitizer().F_SECURING_SYSTEM],
            'mail'                          : [[5], []], 
            'mb_send_mail'                  : [[5], []],
            'w32api_invoke_function'        : [[1], []],
            'w32api_register_function'      : [[2], []],
            }

    class Source:
        VAR_LIST = ["V_USERINPUT"]
        FUNC_LIST = ["F_FILE_INPUT","F_DATABASE_INPUT","F_OTHER_INPUT"]

        V_USERINPUT = [
        '_GET',
        '_POST',
        '_COOKIE',
        '_REQUEST',
        '_FILES',
        '_SERVER',
        'HTTP_GET_VARS',
        'HTTP_POST_VARS',
        'HTTP_COOKIE_VARS',  
        'HTTP_REQUEST_VARS', 
        'HTTP_POST_FILES',
        'HTTP_SERVER_VARS',
        'HTTP_RAW_POST_DATA',
        'argc',
        'argv']

        V_SERVER_PARAMS = [
        'HTTP_ACCEPT',
        'HTTP_ACCEPT_LANGUAGE',
        'HTTP_ACCEPT_ENCODING',
        'HTTP_ACCEPT_CHARSET',
        'HTTP_CONNECTION',
        'HTTP_HOST',
        'HTTP_KEEP_ALIVE',
        'HTTP_REFERER',
        'HTTP_USER_AGENT',
        'HTTP_X_FORWARDED_FOR',
        # all HTTP_ headers can be tainted
        'PHP_AUTH_DIGEST',
        'PHP_AUTH_USER',
        'PHP_AUTH_PW',
        'AUTH_TYPE',
        'QUERY_STRING',
        'REQUEST_METHOD',
        'REQUEST_URI', # partly urlencoded
        'PATH_INFO',
        'ORIG_PATH_INFO',
        'PATH_TRANSLATED',
        'REMOTE_HOSTNAME',
        'PHP_SELF']

        #file content as input
        F_FILE_INPUT = [
        'bzread',
        'dio_read',
        'exif_imagetype',
        'exif_read_data',
        'exif_thumbnail',
        'fgets',
        'fgetss',
        'file', 
        'file_get_contents',
        'fread',
        'get_meta_tags',
        'glob',
        'gzread',
        'readdir',
        'read_exif_data',
        'scandir',
        'zip_read'
        ]

        # database content as input
        F_DATABASE_INPUT = [
        'mysql_fetch_array',
        'mysql_fetch_assoc',
        'mysql_fetch_field',
        'mysql_fetch_object',
        'mysql_fetch_row',
        'pg_fetch_all',
        'pg_fetch_array',
        'pg_fetch_assoc',
        'pg_fetch_object',
        'pg_fetch_result',
        'pg_fetch_row',
        'sqlite_fetch_all',
        'sqlite_fetch_array',
        'sqlite_fetch_object',
        'sqlite_fetch_single',
        'sqlite_fetch_string'
        ]

        # other functions as input
        F_OTHER_INPUT = [
        'get_headers',
        'getallheaders',
        'get_browser',
        'getenv',
        'gethostbyaddr',
        'runkit_superglobals',
        'import_request_variables'
        ]

