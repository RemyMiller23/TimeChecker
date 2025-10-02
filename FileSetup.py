from datetime import datetime, timedelta
import calendar
import os


def generateReport(leave):
    timesheetPath = os.path.join(os.getcwd(), 'ClockingsReport.Txt')

    def format_timedelta_as_hhmmss(td):
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def map_to_incoming_outgoing(description):
        if "Side Door Entry at Server" in description or "Canteen Exit to Stairs" in description or "HO Main Staff IN" in description or "Boom 2 Entry" in description or "Central Sorting Entry" in description or "Procurement Passage Entry" in description or "Canteen Entry from labs" in description:
            return "Incoming"
        if "Canteen Entry from Stairs" in description or "HO Main Staff OUT" in description or "Side Door Exit at Server" in description or "Procurement Passage Exit" in description or "Canteen Exit to labs" in description:
            return "Outgoing"
        return None

    # Set up for output
    report_lines = []

    def append_line(line=""):
        report_lines.append(line)

    # Step 1: Parse and organize
    daily_events = {}

    with open(timesheetPath, 'r') as fileReading:
        for line in fileReading:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            timestamp_str = parts[0]
            description = parts[1] if len(parts) > 1 else ""
            status = map_to_incoming_outgoing(description)

            if status:
                dt = datetime.strptime(timestamp_str, "%Y/%m/%d %a %H:%M:%S")
                date_key = dt.date()
                if date_key not in daily_events:
                    daily_events[date_key] = []
                daily_events[date_key].append((dt, status))

    # Step 1.5: Detect the month and year from dataset
    any_date = next(iter(daily_events))
    year = any_date.year
    month = any_date.month

    # Step 2: Count working days (Mon–Fri)
    working_days = sum(
        1 for day in range(1, calendar.monthrange(year, month)[1] + 1)
        if datetime(year, month, day).weekday() < 5
    )

    working_days -= leave

    # Step 3: Monthly target
    daily_target = timedelta(hours=7, minutes=30)
    monthly_target = working_days * daily_target

    # Step 4: Evaluate progress
    worked_days = 0
    actual_total_worked = timedelta()
    mandatory_deduction = timedelta(minutes=30)

    daily_logs = []
    total_time_on_site = timedelta()
    total_deducted_time = timedelta()

    for date, events in sorted(daily_events.items()):
        events.sort(key=lambda x: x[0])
        first_in = next((dt for dt, status in events if status == "Incoming"), None)
        last_out = next((dt for dt, status in reversed(events) if status == "Outgoing"), None)

        if not first_in or not last_out or last_out <= first_in:
            daily_logs.append(f"{date}: Incomplete or invalid data\n")
            continue

        total_day_duration = last_out - first_in
        total_time_on_site += total_day_duration

        total_break_time = timedelta()
        last_status = None
        last_time = None

        for dt, status in events:
            if dt <= first_in or dt >= last_out:
                continue
            if last_status == "Outgoing" and status == "Incoming":
                total_break_time += dt - last_time
            last_status = status
            last_time = dt

        deducted_time = total_break_time if total_break_time >= mandatory_deduction else mandatory_deduction
        total_deducted_time += deducted_time
        actual_worked_time = total_day_duration - deducted_time
        actual_total_worked += actual_worked_time
        worked_days += 1

        log = [
            f"{date}:",
            f"  ⏱️  Start Time:         {first_in.time()}",
            f"  🛑  End Time:           {last_out.time()}",
            f"  🕒  Total Time On Site: {total_day_duration}",
            f"  🧘  Breaks Taken:       {total_break_time}",
            f"  ⛔  Deducted Time:      {deducted_time}",
            f"  ✅  Actual Worked Time: {actual_worked_time}",
            ""
        ]
        daily_logs.extend(log)

    # Step 5: Summary
    expected_deducted_time = worked_days * mandatory_deduction
    expected_so_far = worked_days * daily_target
    difference = actual_total_worked - expected_so_far
    status_icon = "🟢 Ahead" if difference > timedelta(0) else "🔴 Owing"

    # Build report
    append_line("📅 Monthly Work Target Summary")
    append_line(f"  Month:                  {calendar.month_name[month]} {year}")
    append_line(f"  Working Days:           {working_days}")
    append_line(f"  Target per Day:         {daily_target}")
    append_line(f"  Monthly Target:         {format_timedelta_as_hhmmss(monthly_target)}")
    append_line()

    append_line("📊 Progress Summary (So Far)")
    append_line(f"  Worked Days Logged:     {worked_days}")
    append_line(f"  Expected Time:          {format_timedelta_as_hhmmss(expected_so_far)}")
    append_line(f"  Total Time on Site:     {format_timedelta_as_hhmmss(total_time_on_site)}")
    append_line(f"  Expected Deducted Time: {format_timedelta_as_hhmmss(expected_deducted_time)}")
    append_line(f"  Total Deducted Time:    {format_timedelta_as_hhmmss(total_deducted_time)}")
    append_line(f"  Actual Time Worked:     {format_timedelta_as_hhmmss(actual_total_worked)}")
    append_line(f"  Difference:             {format_timedelta_as_hhmmss(abs(difference))} {status_icon}")
    append_line()

    # Add daily logs
    report_lines.extend(daily_logs)

    # Step 6: Write to file
    today = datetime.today()
    if today.day == 1:
        if today.month == 1:
            RepMonth = 12
            RepYear = today.year - 1
            filename = f"{calendar.month_name[RepMonth]} - {RepYear}.txt"
            output_path = os.path.join(os.getcwd(), filename)
        else:
            RepMonth = today.month - 1
            RepYear = today.year
            filename = f"{calendar.month_name[RepMonth]} - {RepYear}.txt"
            output_path = os.path.join(os.getcwd(), filename)
    else:
        RepMonth = today.month
        RepYear = today.year
        filename = f"{calendar.month_name[RepMonth]} - {RepYear}.txt"
        output_path = os.path.join(os.getcwd(), filename)

    with open(output_path, 'w', encoding='utf-8') as out_file:
        out_file.write('\n'.join(report_lines))

    return print(f"Report written to: {output_path}")