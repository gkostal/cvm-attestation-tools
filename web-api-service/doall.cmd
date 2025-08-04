@rem Do everything!

call docker.build.cmd
call docker.push.cmd
call aks.publish.cmd