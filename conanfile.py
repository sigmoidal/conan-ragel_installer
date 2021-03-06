#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, AutoToolsBuildEnvironment
import os

class RagelConan(ConanFile):
    name = "ragel_installer"
    version = "6.10"
    description = "Ragel compiles executable finite state machines from regular languages. " \
                  "Ragel targets C, C++ and ASM. "
    homepage = "http://www.colm.net/open-source/ragel"

    settings = {"os": ["Windows"],
                "arch": ["x86", "x86_64"],
                "compiler": [ 'Visual Studio', 'gcc' ],
                "build_type": ["Release"]}

    url = "https://github.com/bincrafters/conan-ragel_installer"

    license = "https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html"
    source_url = 'http://www.colm.net/files/ragel/ragel-{0}.tar.gz'.format(version)

    def configure(self):
        if self.settings.compiler == 'Visual Studio':
            self.settings.compiler.runtime = "MT"
            
        self.settings.build_type = "Release"

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.build_requires("msys2_installer/latest@bincrafters/stable")
            
            if self.settings.compiler == 'gcc':
                self.build_requires("mingw_installer/1.0@conan/stable")

    def source(self):
        filename = "ragel-%s.tar.gz" % self.version
        tools.download(self.source_url, filename)
        tools.untargz(filename)
        os.unlink(filename)

    def build(self):
        if 'MSYS_ROOT' not in os.environ:
            os.environ['MSYS_ROOT'] = self.deps_env_info["msys2_installer"].MSYS_ROOT
        
        if 'MSYS_ROOT' not in os.environ:
            raise Exception("MSYS_ROOT environment variable must be set.")
        else:
            self.output.info("Using MSYS from: " + os.environ["MSYS_ROOT"])
               
        
        os.environ['PATH'] = os.path.join(os.environ['MSYS_ROOT'], 'usr', 'bin') + os.pathsep + \
                             os.environ['PATH']
        

        compiler_options = ''
        linker_options = ''
        runtime_options = ''
        ld_options = ''
        nm_options = ''
        ranlib_options = ''
        strip_options = ''
        
        if self.settings.compiler == 'Visual Studio':
            # this overrides pre-configured environments (such as Appveyor's)
            if "VisualStudioVersion" in os.environ:
                del os.environ["VisualStudioVersion"]

            vccmd = tools.vcvars_command(self.settings) + " &&"
            compiler_cc = '$PWD/compile cl -nologo'
            compiler_cxx = compiler_cc
            
        elif self.settings.compiler == 'gcc':
            vccmd = ''
            if 'MINGW_HOME' in os.environ: 
                compiler_cc = tools.unix_path(self.deps_env_info["mingw_installer"].CC)
                compiler_cxx = tools.unix_path(self.deps_env_info["mingw_installer"].CXX)
            else:
                compiler_cc = self.settings.compiler
                compiler_cxx = compiler_cc

        env_build = AutoToolsBuildEnvironment(self)
        with tools.chdir("{0}-{1}".format('ragel', self.version)):
            with tools.environment_append(env_build.vars):

                self.run("bash -c 'pacman -S automake-wrapper autoconf --noconfirm --needed'")

                makefile_am = os.path.join('ragel', 'Makefile.am').replace('\\','/')
                self.output.info("Patching: %s" % makefile_am)
                tools.replace_in_file(makefile_am, 
                                      'INCLUDES = -I$(top_srcdir)/aapl',
                                      'AM_CPPFLAGS = -I$(top_srcdir)/aapl')

                main_cpp = os.path.join('ragel', 'main.cpp').replace('\\','/')
                self.output.info("Patching: %s" % main_cpp)
                tools.replace_in_file(main_cpp, 
                                      '#include <unistd.h>',
                                      '')

                self.run("{vccmd} bash -c 'aclocal'".format(vccmd=vccmd))
                self.run("{vccmd} bash -c 'autoheader'".format(vccmd=vccmd))
                self.run("{vccmd} bash -c 'automake --foreign --add-missing --force-missing'".format(vccmd=vccmd))
                self.run("{vccmd} bash -c 'autoconf'".format(vccmd=vccmd))

                
                if self.settings.compiler == 'Visual Studio':
                    compiler_options = '-D_CRT_SECURE_NO_WARNINGS -D_CRT_SECURE_NO_DEPRECATE ' \
                                       '-D_CRT_NONSTDC_NO_WARNINGS -WL -W2 -WX- -Gy -DNDEBUG ' \
                                       '-diagnostics:classic -DWIN32 -D_WINDOWS -O2 -Ob2 '

                    compiler_options += '-wd4577 -wd5026 -wd5027 -wd4710 -wd4711 -wd4626 -wd4250 -wd4365 ' \
                                        '-wd4625 -wd4774 -wd4530 -wd4100 -wd4706 -wd4512 -wd4800 -wd4702 ' \
                                        '-wd4819 -wd4355 -wd4091 -wd4267 -wd4365 -wd4625 -wd4774 -wd4820'

                    linker_options = '/MACHINE:X{0}'.format('86' if self.settings.arch == 'x86' else '64')
                    runtime_options = '-' + str(self.settings.compiler.runtime)
                    ld_options = 'LD="link" '
                    nm_options = 'NM="dumpbin -symbols" '
                    strip_options = 'STRIP=":" '
                    ranlib_options = 'RANLIB=":" '

                    
                prefix = tools.unix_path(os.path.abspath("../out"))
                self.run('{vccmd} bash -c \'./configure '
                         '--prefix={prefix} '
                         'CC="{compiler_cc}" '
                         'CXX="{compiler_cxx}" '
                         'CFLAGS="{compiler_options} {runtime} -I{prefix}/include " '
                         'CXXFLAGS="{compiler_options} {runtime} -I{prefix}/include " '
                         'CPPFLAGS="{compiler_options} {runtime} -I{prefix}/include " '
                         'LDFLAGS="-L{prefix}/lib {linker_options}" '
                         '{ld_options}'
                         '{nm_options}'
                         '{strip_options}'
                         '{ranlib_options}'
                         '\''.format(vccmd=vccmd, 
                                     prefix=prefix, 
                                     compiler_cc=compiler_cc,
                                     compiler_cxx=compiler_cxx,
                                     ld_options=ld_options,
                                     nm_options=nm_options,
                                     strip_options=strip_options,
                                     ranlib_options=ranlib_options,
                                     compiler_options=compiler_options, 
                                     linker_options=linker_options,
                                     runtime=runtime_options))

                self.run("{vccmd} bash -c 'make -s -j {cpus} install".format(vccmd=vccmd, cpus=tools.cpu_count()))


    def package(self):
        build_src_dir = "{0}-{1}".format('ragel', self.version)
        build_dir = os.path.join('out','bin')

        self.copy(pattern="COPYING", dst="licenses", src=build_src_dir)
        self.copy(pattern="CREDITS", dst="licenses", src=build_src_dir)
        self.copy(pattern="*.exe", dst="bin", src=build_dir, keep_path=False)

    def package_info(self):
        self.env_info.RAGEL_ROOT = self.package_folder
        self.env_info.path.append(os.path.join(self.package_folder, 'bin'))

