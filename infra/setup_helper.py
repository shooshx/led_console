import sys, os, subprocess
import setuptools.command.build_ext

if sys.platform == "linux":
    # patch build_ext for running strip
    # https://jichu4n.com/posts/how-to-add-custom-build-steps-and-commands-to-setuppy/
    # from setuptools\command\build_ext.py
    class BuildExt_withStrip(setuptools.command.build_ext.build_ext):
        def run(self):
            setuptools.command.build_ext.build_ext.run(self)
            build_py = self.get_finalized_command('build_py')
            for ext in self.extensions:
                fullname = self.get_ext_fullname(ext.name)
                filename = self.get_ext_filename(fullname)
                modpath = fullname.split('.')
                package = '.'.join(modpath[:-1])
                package_dir = build_py.get_package_dir(package)
                dest_filename = os.path.join(package_dir, os.path.basename(filename))

                cmd = ['strip', dest_filename]
                print(' '.join(cmd))
                subprocess.check_call(cmd)

    CMDCLASS = {'build_ext': BuildExt_withStrip }
else:
    CMDCLASS = {}