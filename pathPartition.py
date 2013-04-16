import os, sys, shutil
from optparse import OptionParser

def parse_args():
    parser = OptionParser(usage='>pathPartition -p <path> -n <num partitions>')
    
    parser.add_option('-p', '--path', dest='path', action='store',
                      default='.')
    parser.add_option('-n', '--numpartitions', action='store',
                      dest='numpartitions', default=5)
    parser.add_option('-b', '--basename', action='store', dest='basename',
                      default='pathPartition')

    (opts, args) = parser.parse_args()

    return (opts, args)

def get_partition_bounds(partition, partition_num):
    """
    Gets the highest and lowest (alphabetical order) letters of the files in
    the given partition.
    """
    try:
        # Get the first and second letters of the first file.
        first_path, first_name = os.path.split(partition[0])
        first_first = first_name[0]
        first_second = first_name[1]

        # Get the first and second letters of the last file
        last_path, last_name = os.path.split(partition[-1])
        last_first = last_name[0]
        last_second = last_name[1]
        return '%s-%s' % (first_first.upper()+first_second.lower(),
                          last_first.upper()+last_second.lower())

    except IndexError:
        print "Unable to get partition bounds"
        return '%s' % partition_num
    

def main():
    (opts, args) = parse_args()
    
    # Get the user supplied args.
    path = opts.path
    num_partitions = opts.numpartitions
    basename = opts.basename

    # Get a sorted list of files in path
    try:
        files = sorted(os.listdir(path))
        file_count = len(files)
    except OSError:
        print 'Error reading path %s' % e
        sys.exit(0)

    # Partition the files into groups
    partitions = [[] for partition in range(0, num_partitions)]
    files_per_partition = file_count / num_partitions
    partition_index = 0

    for i, f in enumerate(files):
        abs_path = os.sep.join([path, f])
        if i > files_per_partition*(partition_index+1):
            partition_index += 1
        try:
            partitions[partition_index].append(abs_path)
        except IndexError:
            partitions[partition_index-1].append(abs_path)

    # Build the partition names and move the files into the partition.
    for i, partition in enumerate(partitions):
        part_name = get_partition_bounds(partition, i)
        try:
            partition_path = os.sep.join([path, basename+'_'+part_name])
            os.mkdir(partition_path)
            for p_file in partition:
                print 'Copying %s into %s' % (p_file, partition_path)
                shutil.copy(p_file, partition_path)
        except OSError, e:
            print 'Unable to make partition at %s. %s' % (partition_path, e)

if __name__ == '__main__':
    main()

    


