#!/usr/bin/env python3


import os
import sys
import stat
import argparse as ap
import configparser as cp


DB_TYPE_CHOICES = ['n', 'a']
DB_DNA_CHOICES = ['makeblastdb']
DB_AA_CHOICES = ['usearch', 'diamond']
MAP_DNA_CHOICES = ['blastn', 'tblastn', 'diamond']
MAP_AA_CHOICES = ['usearch', 'diamond']
MSA_CHOICES = ['muscle', 'mafft', 'opal', 'upp']
TRIM_CHOICES = ['trimal']
GENE_TREE1_CHOICES = ['fasttree', 'raxml']
GENE_TREE2_CHOICES = ['raxml']
TREE1_CHOICES = ['fasttree', 'raxml', 'astral', 'astrid']
TREE2_CHOICES = ['raxml']


def info(s, init_new_line=False, exit=False, exit_value=0):
    if init_new_line:
        sys.stdout.write('\n')

    sys.stdout.write('{}'.format(s))
    sys.stdout.flush()

    if exit:
        sys.exit(exit_value)


def error(s, init_new_line=False, exit=False, exit_value=1):
    if init_new_line:
        sys.stderr.write('\n')

    sys.stderr.write('[e] {}\n'.format(s))
    sys.stderr.flush()

    if exit:
        sys.exit(exit_value)


def read_params():
    p = ap.ArgumentParser(description="")

    p.add_argument('-o', '--output', type=str, required=True,
                   help=("Specify the output file where to write the configurations. If "
                         "the file already exists the program won't overwrite the alredy "
                         "existing file"))
    p.add_argument('-d', '--db_type', required=True, choices=DB_TYPE_CHOICES,
                   help=("Specify the type of the database, where 'n' stands for "
                         "nucleotides and 'a' for amino acids"))

    p_db = p.add_mutually_exclusive_group(required=True)
    p_db.add_argument('--db_dna', default=None, choices=DB_DNA_CHOICES, help="")
    p_db.add_argument('--db_aa', default=None, choices=DB_AA_CHOICES, help="")

    p.add_argument('--map_dna', default=None, choices=MAP_DNA_CHOICES, help="")
    p.add_argument('--map_aa', default=None, choices=MAP_AA_CHOICES, help="")
    p.add_argument('--msa', required=True, default=None, choices=MSA_CHOICES, help="")
    p.add_argument('--trim', default=None, choices=TRIM_CHOICES,
                   help="Specify to add the trim section")
    p.add_argument('--gene_tree1', default=None, choices=GENE_TREE1_CHOICES,
                   help="Specify to add the gene_tree1 section")
    p.add_argument('--gene_tree2', default=None, choices=GENE_TREE2_CHOICES,
                   help="Specify to add the gene_tree2 section")
    p.add_argument('--tree1', required=True, default=None, choices=TREE1_CHOICES,
                   help="Specify to add the tree2 section")
    p.add_argument('--tree2', default=None, choices=TREE2_CHOICES,
                   help="Specify to add the tree2 section")
    p.add_argument('--overwrite', action='store_true', default=False,
                   help="If output file exists it will be overwritten")
    p.add_argument('--verbose', action='store_true', default=False,
                   help="Prints more stuff")

    return p.parse_args()


def check_params(args):
    if (not args.map_dna) and (not args.map_aa):
        error('at least one of --map_dna and --map_aa must be specified', exit=True)

    if (os.path.isfile(args.output)) and (not args.overwrite):
        error('cannot write ouptut file {} because it already exists'.format(args.output),
              exit=True)


def find_executable(exe, rollback=False):
    current_env = os.environ.copy()

    if 'PATH' in current_env:
        for d in current_env['PATH'].split(':'):
            for f in os.listdir(d):
                e = os.path.realpath(os.path.join(d, f))

                if (os.path.exists(e) and (not os.path.isdir(e)) and
                        bool(os.stat(e)[stat.ST_MODE] & stat.S_IXUSR)):
                    if exe.lower() in e.lower():
                        return (f, True if not rollback else False)

    if rollback:
        find_executable(rollback, rollback=True)

    error('could not find "{}" executable in your PATH environment variable', exit=True)


# AVAILABLE OPTIONS:
# program_name: name of the executable to use
# params: params to use
# threads: specify the option to use to pass the number of threads
# input: specify the option to use for the input file
# database: specify the option to use for setting the database
# output_path: specify the to option to use to set the path of the folder that will
#              contains the output file
# output: specify the option to use for the output file
# version: specify the option to use to get the version of the software, used to verify
#          the software installation
# command_line: specify the command line to generate with the position of each argument,
#               '<' and '>' can be used to specify input/output redirection, respectively
# environment: specify variables and their values to be defined in the environment,
#              syntax VARIABLE1=VALUE1,VARIABLE2=VALUE2,...


if __name__ == '__main__':
    args = read_params()
    check_params(args)
    progs = {}

    # setting the program for building the nucleotides DB
    if args.db_dna:
        if 'makeblastdb' in args.db_dna:
            exe, _ = find_executable('makeblastdb')
            db_dna = {'program_name': exe,
                      'params': '-parse_seqids -dbtype nucl',
                      'input': '-in',
                      'output': '-out',
                      'version': '-version',
                      'command_line': '#program_name# #params# #input# #output#'}

        progs['db_dna'] = db_dna

    # setting the program for building the amino acids DB
    if args.db_aa:
        if 'usearch' in args.db_aa:
            exe, _ = find_executable('usearch')
            db_aa = {'program_name': exe,
                     'params': '-quiet',
                     'input': '-makeudb_ublast',
                     'output': '-output',
                     'version': '-version',
                     'command_line': '#program_name# #params# #input# #output#'}
        elif 'diamond' in args.db_aa:
            exe, _ = find_executable('diamond')
            db_aa = {'program_name': exe,
                     'params': 'makedb',
                     'threads': '--threads',
                     'input': '--in',
                     'output': '--db',
                     'version': 'version',
                     'command_line': '#program_name# #params# #threads# #input# #output#'}

        progs['db_aa'] = db_aa

    # setting the software for mapping the genomes (dna)
    if args.map_dna:
        if 'blastn' in args.map_dna:
            exe, _ = find_executable('blastn')
            map_dna = {'program_name': exe,
                       'params': '-outfmt 6 -max_target_seqs 1000000',
                       'input': '-query',
                       'database': '-db',
                       'output': '-out',
                       'version': '-version',
                       'command_line': ('#program_name# #params# #input# #database# '
                                        '#output#')}
        elif 'tblastn' in args.map_dna:
            exe, _ = find_executable('tblastn')
            map_dna = {'program_name': exe,
                       'params': ('-outfmt "6 saccver qaccver pident length mismatch '
                                  'gapopen sstart send qstart qend evalue bitscore" '
                                  '-evalue 1e-50 -max_target_seqs 1000000'),
                       'input': '-subject',
                       'database': '-query',
                       'output': '-out',
                       'version': '-version',
                       'command_line': ('#program_name# #params# #input# #database# '
                                        '#output#')}
        elif 'diamond' in args.map_dna:
            exe, _ = find_executable('diamond')
            map_dna = {'program_name': exe,
                       'params': ('blastx --quiet --threads 1 --outfmt 6 --more-sensitive '
                                  '--id 50 --max-hsps 35 -k 0'),
                       'input': '--query',
                       'database': '--db',
                       'output': '--out',
                       'version': 'version',
                       'command_line': ('#program_name# #params# #input# #database# '
                                        '#output#')}

        progs['map_dna'] = map_dna

    # setting the software for mapping the proteomes (aa)
    if args.map_aa:
        if 'usearch' in args.map_aa:
            exe, _ = find_executable('usearch')
            map_aa = {'program_name': exe,
                      'params': '-quiet -evalue 1e-10 -maxaccepts 8 -maxrejects 32',
                      'threads': '-threads',
                      'input': '-ublast',
                      'database': '-db',
                      'output': '-blast6out',
                      'version': '-version',
                      'command_line': ('#program_name# #params# #threads# #input# '
                                       '#database# #output#')}
        elif 'diamond' in args.map_aa:
            exe, _ = find_executable('diamond')
            map_aa = {'program_name': exe,
                      'params': ('blastp --quiet --threads 1 --outfmt 6 --more-sensitive '
                                 '--id 50 --max-hsps 35 -k 0'),
                      'input': '--query',
                      'database': '--db',
                      'output': '--out',
                      'version': 'version',
                      'command_line': '#program_name# #params# #input# #database# #output#'}

        progs['map_aa'] = map_aa

    # setting the MSA software
    if 'muscle' in args.msa:
        exe, _ = find_executable('muscle')
        msa = {'program_name': exe,
               'params': '-quiet -maxiters 2',
               'input': '-in',
               'output': '-out',
               'version': '-version',
               'command_line': '#program_name# #params# #input# #output#'}
    elif 'mafft' in args.msa:
        exe, _ = find_executable('mafft')
        msa = {'program_name': exe,
               'params': '--quiet --anysymbol --auto',
               'environment': 'TMPDIR=/local-storage',
               'version': '--version',
               'command_line': '#program_name# #params# #input# > #output#'}
    elif 'opal' in args.msa:
        exe, _ = find_executable('opal')
        msa = {'program_name': exe,
               'input': '--in',
               'output': '--out',
               'params': '--quiet',
               'command_line': '#program_name# #params# #input# #output#'}

        if args.db_type == 'a':
            msa['params'] += ' --protein'
    elif 'upp' in args.msa:
        exe, _ = find_executable('run-upp.sh', rollback='upp')
        msa = {'program_name': exe,
               'params': '-x 1 -M -1 -T 0.66 -B 999999999',
               'input': '-s',
               'output': '-o',
               'output_path': '-d',
               'version': '--version',
               'command_line': '#program_name# #params# #input# #output_path# #output#'}

        if args.db_type == 'n':
            msa['params'] += ' -m dna',
        elif args.db_type == 'a':
            msa['model'] += ' -m amino'

    progs['msa'] = msa

    # setting the trimming software
    if args.trim:
        if 'trimal' in args.trim:
            exe, _ = find_executable('trimal')
            trim = {'program_name': exe,
                    'params': '-gappyout',
                    'input': '-in',
                    'output': '-out',
                    'version': '--version',
                    'command_line': '#program_name# #params# #input# #output#'}

        progs['trim'] = trim

    # setting gene_tree1
    if args.gene_tree1:
        if 'fasttree' in args.gene_tree1:
            exe, _ = find_executable('FastTree-2.1.9-SSE3', rollback='fasttree')
            gene_tree1 = {'program_name': exe,
                          'params': ('-quiet -mlacc 2 -slownni -spr 4 -fastest -mlnni 4 '
                                     '-no2nd'),
                          'output': '-out',
                          'command_line': '#program_name# #params# #output# #input#'}

            if args.db_type == 'n':
                gene_tree1['params'] += ' -gtr -nt'
            elif args.db_type == 'a':
                gene_tree1['params'] += ' -lg'
        elif 'raxml' in args.gene_tree1:
            exe, _ = find_executable('raxmlHPC', rollback='raxml')
            gene_tree1 = {'program_name': exe,
                          'params': '-p 1989',
                          'input': '-s',
                          'output_path': '-w',
                          'output': '-n',
                          'version': '-v'}

            if args.db_type == 'n':
                gene_tree1['params'] += ' -m GTRCAT',
                gene_tree1['command_line'] = ('#program_name# #params# #output_path# '
                                              '#input# #output#')
            elif args.db_type == 'a':
                gene_tree1['model'] = '-m'
                gene_tree1['command_line'] = ('#program_name# #model# #params# '
                                              '#output_path# #input# #output#')

        progs['gene_tree1'] = gene_tree1

    # setting gene_tree2
    if args.gene_tree2:
        if 'raxml' in args.gene_tree2:
            exe, _ = find_executable('raxmlHPC', rollback='raxml')
            gene_tree2 = {'program_name': exe,
                          'params': '-p 1989',
                          'database': '-t',  # starting tree
                          'input': '-s',
                          'output_path': '-w',
                          'output': '-n',
                          'version': '-v'}

            if args.db_type == 'n':
                gene_tree2['params'] += '-p 1989 -m GTRCAT'
                gene_tree2['command_line'] = ('#program_name# #params# #database# '
                                              '#output_path# #input# #output#')
            elif args.db_type == 'a':
                gene_tree2['model'] = '-m'
                gene_tree2['command_line'] = ('#program_name# #model# #params# '
                                              '#database# #output_path# #input# #output#')

        progs['gene_tree2'] = gene_tree2

    # setting tree1
    if 'astral' in args.tree1:
        tree1 = {'program_name': 'java -jar /CM/tools/astral-4.11.1/astral.4.11.1.jar',
                 'input': '-i',
                 'output': '-o',
                 # 'version': '--help',
                 'version': '-i /CM/tools/astral-4.11.1/test_data/song_mammals.424.gene.tre',
                 'command_line': '#program_name# #input# #output#'}
    if 'astrid' in args.tree1:
        exe, _ = find_executable('ASTRID')
        tree1 = {'program_name': exe,
                 'input': '-i',
                 'params': '-m auto',
                 'output': '-o',
                 'version': '--help',
                 'command_line': '#program_name# #input# #params# #output#'}
    elif 'fasttree' in args.tree1:
        exe, rb = find_executable('FastTreeMP-2.1.9-SSE3', rollback='fasttree')
        tree1 = {'program_name': exe,
                 'params': '-quiet -mlacc 2 -slownni -spr 4 -fastest -mlnni 4 -no2nd',
                 'output': '-out',
                 'command_line': '#program_name# #params# #output# #input#'}
        if not rb:
            tree1['environment'] = 'OMP_NUM_THREADS=3'

        if args.db_type == 'n':
            tree1['params'] += ' -gtr -nt'
        elif args.db_type == 'a':
            tree1['params'] += ' -lg'
    elif 'raxml' in args.tree1:
        exe, rb = find_executable('raxmlHPC-PTHREADS-SSE3', rollback='raxml')
        tree1 = {'program_name': exe,
                 'params': '-p 1989',
                 'input': '-s',
                 'output_path': '-w',
                 'output': '-n',
                 'version': '-v',
                 'command_line': ('#program_name# #params# #threads# #database# '
                                  '#output_path# #input# #output#')}
        if not rb:
            tree1['threads'] = '-T'

        if args.db_type == 'n':
            tree1['params'] += ' -m GTRCAT'
        elif args.db_type == 'a':
            tree1['params'] += ' -m PROTCATLG'

    progs['tree1'] = tree1

    # setting tree2
    if args.tree2:
        if 'raxml' in args.tree2:
            exe, rb = find_executable('raxmlHPC-PTHREADS-SSE3', rollback='raxml')
            tree2 = {'program_name': exe,
                     'params': '-p 1989',
                     'database': '-t',  # starting tree
                     'input': '-s',
                     'output_path': '-w',
                     'output': '-n',
                     'version': '-v',
                     'command_line': ('#program_name# #params# #threads# #database# '
                                      '#output_path# #input# #output#')}
            if not rb:
                tree2['threads'] = '-T'

            if args.db_type == 'n':
                tree2['params'] += ' -m GTRCAT'
            elif args.db_type == 'a':
                tree2['params'] += ' -m PROTCATLG'

        progs['tree2'] = tree2

    config = cp.ConfigParser()

    for prog, options in progs.items():
        config[prog] = {}

        for option, value in options.items():
            config[prog][option] = value

    if (os.path.isfile(args.output)) and args.overwrite and args.verbose:
        info('Output file "{}" will be overwritten\n'.format(args.output))

    with open(args.output, 'w') as f:
        config.write(f)

    sys.exit(0)