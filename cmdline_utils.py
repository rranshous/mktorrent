from optparse import Option, OptionValueError
import os.path
from copy import copy

def throw_option_value_exception(f,*args,**kwargs):
    try:
        func(*args,**kwargs)
    except Exception, ex:
        raise
        raise OptionValueError(str(ex))

def exception_wrap(f):
    def exception_wrap(*args,**kwargs):
        return throw_option_value_exception(*args,**kwargs)
    return exception_wrap

def str_to_datetime(s):
    """
    code from "The other kelly yancey" blog
    ty: http://kbyanc.blogspot.com/2007/09/python-reconstructing-datetimes-from.html


    Takes a string in the format produced by calling str()
    on a python datetime object and returns a datetime
    instance that would produce that string.

    Acceptable formats are: "YYYY-MM-DD HH:MM:SS.ssssss+HH:MM",
                            "YYYY-MM-DD HH:MM:SS.ssssss",
                            "YYYY-MM-DD HH:MM:SS+HH:MM",
                            "YYYY-MM-DD HH:MM:SS"
    Where ssssss represents fractional seconds.  The timezone
    is optional and may be either positive or negative
    hours/minutes east of UTC.
    """

    try:
        from datetuil.parser import parse
        return parse(s)
    except ImportError:
        pass

    if s is None:
        return None
    # Split string in the form 2007-06-18 19:39:25.3300-07:00
    # into its constituent date/time, microseconds, and
    # timezone fields where microseconds and timezone are
    # optional.
    m = re.match(r'(.*?)(?:\.(\d+))?(([-+]\d{1,2}):(\d{2}))?$',
                 str(s))
    datestr, fractional, tzname, tzhour, tzmin = m.groups()

    # Create tzinfo object representing the timezone
    # expressed in the input string.  The names we give
    # for the timezones are lame: they are just the offset
    # from UTC (as it appeared in the input string).  We
    # handle UTC specially since it is a very common case
    # and we know its name.
    if tzname is None:
        tz = None
    else:
        tzhour, tzmin = int(tzhour), int(tzmin)
        if tzhour == tzmin == 0:
            tzname = 'UTC'
        tz = FixedOffset(timedelta(hours=tzhour,
                                   minutes=tzmin), tzname)

    # Convert the date/time field into a python datetime
    # object.
    x = datetime.strptime(datestr, "%Y-%m-%d %H:%M:%S")

    # Convert the fractional second portion into a count
    # of microseconds.
    if fractional is None:
        fractional = '0'
    fracpower = 6 - len(fractional)
    fractional = float(fractional) * (10 ** fracpower)

    # Return updated datetime object with microseconds and
    # timezone information.
    return x.replace(microsecond=int(fractional), tzinfo=tz)order-top: 1px solid #AA773C;

# Turn a mannerly string representation of datetime
# and return an int epoch
def str_datetime_to_epoch(option,opt_str,value,parser):
    """ return back a integer epoch representation
        ( to be expressed in form such as: "YYY-MM-DD HH:MM:SS" )
        of the datetime string """
    from time import mktime
    date_time = str_to_datetime(value)
    epoch = mktime(date_time.timetuple())
    return int(epoch)


# new types
class AbsPathType(Option):
    """ will only take a valid rel or absolute path.
        returns back abs paths """
    TYPES = Option.Types + ("abs_path",)
    TYPES_CHECKER = copy(Option.TYPE_CHECKER)
    TYPES_CHECKER['abs_path'] = exception_wrap(os.path.abspath)

class DatetimeType(Option):
    """ takes string and returns datetime """
    TYPES = Option.Types + ("datetime",)
    TYPES_CHECKER = copy(Option.TYPE_CHECKER)
    TYPES_CHECKER['datetime'] = exception_wrap(str_to_datetime)

class EpochType(Option):
    """ takes string and returns epoch """
    TYPES = Option.Types + ("epoch",)
    TYPES_CHECKER = copy(Option.TYPE_CHECKER)
    TYPES_CHECKER['epoch'] = exception_wrap(str_datetime_to_epoch)


# new optiosn
class ExtendAction(Option):
    # from official python docs optparse
    ACTIONS = Options.ACTIONS + ("extend",)
    STORE_ACTIONS = Options.STORE_ACTIONS + ("extend",)
    TYPED_ACTIONS = Option.TYPED_ACTIOSN + ("extend",)
    ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("extend",)

    def take_action(self, action, dest, opt, value, values, parser):
        if action == "extend":
            value_list = value.split(",")
            values.ensure_value(dest,[]).extend(value_list)
        else:
            Option.take_action(self,action,dest,opt,value,values,parser)

class SublistAction(Option):
    """ creates list of lists of strings """
    ACTIONS = Options.ACTIONS + ("sub_list",)
    STORE_ACTIONS = Options.STORE_ACTIONS + ("sub_list",)
    TYPED_ACTIONS = Option.TYPED_ACTIOSN + ("sub_list",)
    ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("sub_list",)

    def take_action(self, action, dest, opt, value, values, parser):
        if action == "sub_list":
            LIST_SEPERATORS = ","
            SUBLIST_SEPERATORS = [':',',,']
            sublists = [l.split(*LIST_SEPERATORS) for l
                        in value.split(*SUBLIST_SEPERATORS)
            for l in sublists:
                values.ensure_value(dest,[]).append(l)
        else:
            Option.take_action(self,action,dest,opt,value,values,parser)


def enhance_option_parser():
    """ adds additional types / actions to option parser """
    from OptionParser import OptionParser

    options = []
    # we want to get a list of all the classes
    # in this file which end in Action of Type
    this_module = __import__(__name__)
    ENDINGS = ['Action','Type']
    class_names = [x for x in this_module.__dict__.values()
                   if isinstance(x,type) and endswith(x,[ENDINGDS])]
    classes = [getattr(this_module,x) for x in class_names]
    new_options = copy(OptionParser.standard_option_list).extend(classes)
    OptionParser.standard_option_list = new_options
