Matterhorn-Module
=================

For the automatic export of Matterhorn recordings to the
Matterhorn-Lernfunk-Importer you can use the
workflowoperation-mediapackage-post Matterhorn module which can be found at:

   https://github.com/lkiesow/matterhorn-workflowoperation-mediapackagepost

If you use the Matterhorn RPM Repository provided by the Universtiy of
Osnabrück, you can simply install the module from the repo::

   % yum install opencast-matterhorn14-module-workflowoperation-mediapackagepost

The module can be integrated into any Matterhorn Workflows to send a mediapacke
to a foreign webservice.  The configuration for the workflow operation should
look like this::

   <!-- 
      This operation will send a POST request containing the Mediapackage to an
      external webservice.
   -->
   <operation
      id="post-mediapackage"
      fail-on-error="false"
      exception-handler-workflow="error"
      description="Sending MediaPackage to Lernfunk3">
      <configurations>
         <!-- target url --> 
         <configuration key="url">http://example.com:5000/</configuration>
         <!-- Use xml as export format --> 
         <configuration key="format">xml</configuration>
         <!-- 
            Disable this on a productive system. if enabled, request bodies
            etc. will be written to log. Is disabled, only errors will be
            logged.
         --> 
         <configuration key="debug">no</configuration>
         <!-- enable authentication (simple/digest will be detected automatically) --> 
         <configuration key="auth.enabled">yes</configuration>
          <!-- username for authentication --> 
         <configuration key="auth.username">exportuser</configuration>
         <!-- password for authentication --> 
         <configuration key="auth.password">secret</configuration>
         <!-- fields with keys beginning with + will be added to the message body --> 
         <configuration key="+source_system">video.example.com</configuration>  
      </configurations>
   </operation>
