import time

MONTH_ALIASES = {
    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4,
    'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8,
    'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12,
}
DOW_ALIASES = {
    'SUN': 0, 'MON': 1, 'TUE': 2, 'WED': 3,
    'THU': 4, 'FRI': 5, 'SAT': 6
}

CRON_ALIASES = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}


def month_days(year, month):
    # Returns number of days in month (for leap years)
    if month == 2:
        return 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
    if month in (1, 3, 5, 7, 8, 10, 12): return 31
    return 30


class Cron:
    def __init__(self, expr):
        expr = expr.strip()
        # Disallow patterns with unsupported features at the earliest point
        if any(x in expr for x in ["L", "W", "#"]):
            raise ValueError("Unsupported feature in cron expression: 'L', 'W', or '#'")
        if expr.startswith('@'):
            if expr.lower() in CRON_ALIASES:
                expr = CRON_ALIASES[expr.lower()]
            else:
                raise ValueError("Unknown cron alias: %s" % expr)
        fields = expr.strip().split()
        if len(fields) != 5:
            raise ValueError("Use standard 5-part cron (min hour dom mon dow)")
        self.minute = self.parse_field(fields[0], 0, 59)
        self.hour = self.parse_field(fields[1], 0, 23)
        self.dom = self.parse_field(fields[2], 1, 31)
        self.month = self.parse_field(fields[3], 1, 12, field_type='month')
        self.dow = self.parse_field(fields[4], 0, 7, field_type='dow')
        self.orig_expr = expr

    def parse_field(self, field, min_val, max_val, field_type=None):
        result_set = set()
        aliases = {}
        if field_type == 'dow':
            aliases = DOW_ALIASES
        elif field_type == 'month':
            aliases = MONTH_ALIASES
        for part in field.upper().split(','):
            # Explicitly reject unsupported features here too, just in case
            if any(x in part for x in ['L', 'W', '#']):
                raise ValueError("Unsupported feature in cron field: 'L', 'W', or '#'")
            step = 1
            if '/' in part:
                range_part, step_str = part.split('/')
                step = int(step_str)
            else:
                range_part = part
            if '-' in range_part:
                start_str, end_str = range_part.split('-')
                start = aliases.get(start_str, start_str)
                end = aliases.get(end_str, end_str)
                start = int(start)
                end = int(end)
                result_set.update(range(start, end + 1, step))
            elif range_part == '*':
                result_set.update(range(min_val, max_val + 1, step))
            else:
                val = aliases.get(range_part, range_part)
                result_set.add(int(val))
        return result_set

    def next_run(self, after=None):
        if after is None:
            after = time.time()
        t = time.localtime(after)
        year, month, day, hour, minute = t[0], t[1], t[2], t[3], t[4]  # start at current minute

        minutes = sorted(self.minute)
        hours = sorted(self.hour)
        doms = sorted(self.dom)
        months = sorted(self.month)
        dows = sorted(self.dow)

        def next_val(allowed, current):
            for v in allowed:
                if v >= current:
                    return v, False
            return allowed[0], True

        # To prevent infinite loops, search at most 5 years ahead
        while year < t[0] + 5:
            # Month
            m, carry = next_val(months, month)
            if carry:
                year += 1
                month, day, hour, minute = months[0], doms[0], hours[0], minutes[0]
                continue
            month = m

            # Days in this month
            dim = month_days(year, month)
            day = max(day, 1)

            # Day
            found = False
            for d in doms:
                if d >= day and d <= dim:
                    day = d
                    found = True
                    break
            if not found:
                month += 1
                day, hour, minute = doms[0], hours[0], minutes[0]
                continue

            # Hour
            h, carry = next_val(hours, hour)
            if carry:
                day += 1
                hour, minute = hours[0], minutes[0]
                continue
            hour = h

            # Minute
            mi, carry = next_val(minutes, minute)
            if carry:
                hour += 1
                minute = minutes[0]
                continue
            minute = mi

            try:
                ttup = (year, month, day, hour, minute, 0, 0, 0, -1)
                run_time = time.mktime(ttup)
                run_struct = time.localtime(run_time)
                py_dow = run_struct[6]  # Monday=0..Sunday=6
                cron_dow = (py_dow + 1) % 7  # Sunday=0
                # Match DOW if needed
                if run_struct[2] == day and (cron_dow in dows or (7 in dows and cron_dow == 0)):
                    if run_time > after:
                        return run_time
            except Exception:
                # Invalid date
                day += 1
                hour, minute = hours[0], minutes[0]
                continue

            # Try next minute
            minute += 1

        return None
