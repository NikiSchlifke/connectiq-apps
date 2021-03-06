#
# This script will parse and output a filtered version
# of a given log file generated by the LogMonkey Connect
# IQ Monkey Barrel. See the print_help() function for details.
#

import getopt
import sys
import re
import os.path

LOG_FILE_OUTPUT_FORMAT = "({0})[{1}] {{{2}}} {3}: {4}"
CSV_FILE_OUTPUT_FORMAT = "{0},{1},{2},{3}"
LOG_LINE_PATTERN = re.compile("^\(lmf([0-9])+\)\[[0-9: -]{19}\] \{\\w+\} [^:]+: .*$")
LOG_LEVEL_WIDTH = 0
TAG_WIDTH = 0

#
# Prints a help message for this script
#
def print_help():
    print '''
Main Page:
    https://github.com/garmin/connectiq-apps/tree/master/barrels/LogMonkey
Description:
    This script takes log files generated by the LogMonkey Connect
    IQ Monkey Barrel as input, parses them and then outputs the parsed
    content.
Arguments:
    Pass a list of log files to parse:
    log_file1.txt log_file2.txt
Options:
    '-l logLevel'   : The log level to filter on.
    '-t tag_values' : The tag value(s) to filter on. Values should be separated by
                      commas. Tag values with a space should be wrapped in quotes.
    '-o output_file': The file to write output to instead of standard out. The values
                      will be output in the same (potentially formatted) output format
                      unless the provided file is a .csv file in which case the fields
                      will be csv formatted.
    '-s'            : If this flag is set the output format will make the columns spacing
                      equivalent throughout the file.
    '-h'            : Prints this message.
Example:
    python parse_log_file -l D -t tag myLog.txt
    '''

#
# A class which holds information about a line in a log file.
#
class LogLine:

    #
    # Creates a new LogLine object.
    #
    # @param rawValue The raw log value this object represents
    # @param logFormat The log format of this line
    # @param timestamp The timestamp from the line
    # @param logLevel The log level of the line
    # @param tag The tag value of the line
    # @param message The message from the line
    #
    def __init__(self, rawValue, logFormat, timestamp, logLevel, tag, message):
        self.rawValue = rawValue
        self.logFormat = logFormat
        self.timestamp = timestamp
        self.logLevel = logLevel
        self.tag = tag
        self.message = message

    def __str__(self):
        return self.rawValue.strip()

    #
    # Checks if this line matches the given log level and tag filters
    #
    # @param logLevel The log level we're filtering for
    # @param tagFilter The tag(s) we're looking for
    # @return True if the line matches the given log level and tag(s)
    #
    def matches_filters(self, logLevel, tagFilter):
        # Check against the log level first
        if logLevel is not None and logLevel != self.logLevel:
            return False

        # Check against the tag filter list
        if tagFilter is not None and self.tag not in tagFilter:
            return False

        # By default the log level will match
        return True

    #
    # Returns a formatted line that conforms to the given width values
    #
    # @param logLevelWidth The number of characters wide the log level value should be
    # @param tagWidth The number of characters wide the tag value should be
    # @return A formatted log line
    #
    def to_spaced_string(self, logLevelWidth, tagWidth):
        formattedLogFormat = self.logFormat
        formattedTimestamp = self.timestamp
        formattedLogLevel = ("{:<" + str(logLevelWidth) + "}").format(self.logLevel)
        formattedTag = ("{:<" + str(tagWidth) + "}").format(self.tag)
        formattedMessage = self.message
        return LOG_FILE_OUTPUT_FORMAT.format(formattedLogFormat, formattedTimestamp, formattedLogLevel, formattedTag, formattedMessage)

    #
    # Returns the log line formatted as CSV format
    #
    # @return The log line formatted to a CSV entry
    #
    def to_csv_string(self):
        formattedTimestamp = self.timestamp
        if "," in formattedTimestamp:
            formattedTimestamp = "\"" + formattedTimestamp + "\""
        formattedLogLevel = self.logLevel
        if "," in formattedLogLevel:
            formattedLogLevel = "\"" + formattedLogLevel + "\""
        formattedTag = self.tag
        if "," in formattedTag:
            formattedTag = "\"" + formattedTag + "\""
        formattedMessage = self.message
        if "," in formattedMessage:
            formattedMessage = "\"" + formattedMessage + "\""
        return CSV_FILE_OUTPUT_FORMAT.format(formattedTimestamp, formattedLogLevel, formattedTag, formattedMessage);

    #
    # Outputs the given LogLine. If the given output file isn't None
    # the line will be printed to that file or else it will be printed
    # to standard output.
    #
    # @param outputFile The output file to write the log line tobytes
    # @param spaceColumns True if the columns should be uniformly spaced
    #
    def output_log_line(self, outputFile, spaceColumns):
        if outputFile is not None:
            if os.path.splitext(outputFile.name)[1][1:] == "csv":
                outputFile.write(self.to_csv_string())
            elif spaceColumns:
                outputFile.write(self.to_spaced_string(LOG_LEVEL_WIDTH, TAG_WIDTH))
            else:
                outputFile.write(str(self))
            outputFile.write("\n")
        else:
            if spaceColumns:
                print self.to_spaced_string(LOG_LEVEL_WIDTH, TAG_WIDTH)
            else:
                print str(self)

#
# Reads through the given input file and parses the lines that are
# valid LogMonkey log lines.
#
# @param path The path to the input log file to read
# @param logLevel The log level we're looking for
# @param tagFilter The tag(s) we're looking for
# @return A list of LogLine objects read from the file
#
def read_through_input_file(path, logLevel, tagFilter):
    logLines = []
    global LOG_LEVEL_WIDTH
    global TAG_WIDTH
    with open(path) as input:
        for line in input:
            # Check to make sure the line is a valid log entry
            if LOG_LINE_PATTERN.match(line):
                logLine = parse_log_line(line)

                # Check the line against the filter options. If the line matches
                # the filter options then output the line
                if logLine.matches_filters(logLevel, tagFilter):
                    logLines.append(logLine)

                    # Check if we need to update the log level or tag width
                    if len(logLine.logLevel) > LOG_LEVEL_WIDTH:
                        LOG_LEVEL_WIDTH = len(logLine.logLevel)
                    if len(logLine.tag) > TAG_WIDTH:
                        TAG_WIDTH = len(logLine.tag)
    return logLines

#
# Parses the given raw log line into a LogLine object
#
# @param line The raw log line to parse
# @return The LogLine object which represents the given log line
#
def parse_log_line(line):
    # The log format is wrapped in parenthesis
    startIndex = line.find("(")+1
    endIndex = line.find(")", startIndex)
    logFormat = line[startIndex:endIndex]

    # The timestamp is wrapped in square brackets
    startIndex = line.find("[")+1
    endIndex = line.find("]", startIndex)
    timestamp = line[startIndex:endIndex]

    # The log level is wrapped in curly brackets
    startIndex = line.find("{", endIndex)+1
    endIndex = line.find("}", startIndex)
    logLevel = line[startIndex:endIndex]

    # The tag follows the log level and ends with a colon
    startIndex = endIndex+1
    endIndex = line.find(":", startIndex)
    tag = line[startIndex:endIndex].strip()

    # The message is the rest of the line
    startIndex = endIndex+1
    message = line[startIndex:].strip()

    return LogLine(line, logFormat, timestamp, logLevel, tag, message)

#
# The main function of the script. This function will parse the
# arguments to the script and call the necessary functions to
# generate the filtered output.
#
def main():
    # These are the local variables we need to populate from the
    # command line arguments/options.
    inputPaths = None
    outputFile = None
    tagFilter = None
    logLevel = None
    spaceColumns = False

    # Check argument list
    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'o:l:t:sh')

        # Get the input files from the argument list
        inputPaths = args

        # Make sure at least one input path value was provided
        if inputPaths is None:
            print "No input path(s) provided"
            exit(2)
        else:
            # Make sure all of the provided input paths are valid
            for path in inputPaths:
                if not os.path.isfile(path):
                    print "Path isn't valid: " + path
                    exit(3)

        # Go through the option values
        for option, arg in optlist:
            if option == "-o":
                outputFile = arg
            elif option == "-l":
                logLevel = arg
            elif option == "-t":
                tagFilter = arg.split(",")
            elif option == "-s":
                spaceColumns = True
            elif option == "-h":
                print_help()
                exit(0)

    # If there was a problem processing the arguments to the script
    # then exit here.
    except getopt.GetoptError as err:
        print(err)
        print_help()
        exit(1)

    # Read through each of the input files and parse the log entries
    logLines = []
    for path in inputPaths:
        logLines = list(logLines + read_through_input_file(path, logLevel, tagFilter))

    # Output to file if one was provided
    if outputFile is not None:
        with open(outputFile, "w") as file:
            for line in logLines:
                line.output_log_line(file, spaceColumns)
    else:
        for line in logLines:
            line.output_log_line(None, spaceColumns)

if __name__ == '__main__':
    main()
