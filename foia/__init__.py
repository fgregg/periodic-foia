import datetime
import os
import sys

import click
import frontmatter
import muckrock

# Initialize MuckRock client
client = muckrock.MuckRock(token=os.getenv("MUCKROCK_API_KEY"))


def yearly_dates():

    current_date = datetime.date.today()

    previous_year = str(
        (datetime.date(current_date.year, 1, 1) - datetime.timedelta(days=1)).year
    )

    return {"previous_year": previous_year, "current_year": str(current_date.year)}


def fiscal_year_dates():

    current_date = datetime.date.today()

    if current_date.month >= 7:
        fiscal_year_start_date = datetime.date(current_date.year - 1, 7, 1)
        fiscal_year_end_date = datetime.date(current_date.year, 6, 30)
    else:
        fiscal_year_start_date = datetime.date(current_date.year - 2, 7, 1)
        fiscal_year_end_date = datetime.date(current_date.year - 1, 6, 30)

    return {
        "previous_fiscal_year_start": fiscal_year_start_date.strftime("%B %d, %Y"),
        "previous_fiscal_year_end": fiscal_year_end_date.strftime("%B %d, %Y"),
        "previous_fiscal_year": f"Fiscal Year {fiscal_year_end_date.year}",
    }


def quarterly_dates(reference_date=None):

    # Use the current date as reference if none is provided
    if not reference_date:
        reference_date = datetime.date.today()

    # Calculate the current quarter
    current_quarter = (reference_date.month - 1) // 3 + 1

    # Find the year and first month of the previous quarter
    if current_quarter == 1:
        # Previous quarter is the last quarter of the previous year
        year = reference_date.year - 1
        first_month_previous_quarter = 10
        previous_quarter = 4
    else:
        # Previous quarter is in the same year
        year = reference_date.year
        first_month_previous_quarter = (current_quarter - 2) * 3 + 1
        previous_quarter = current_quarter - 1

    # First day of the previous quarter
    first_day_previous_quarter = datetime.date(year, first_month_previous_quarter, 1)

    # Last day of the previous quarter
    last_month_previous_quarter = first_month_previous_quarter + 2
    if last_month_previous_quarter == 12:
        last_day_previous_quarter = datetime.date(year, 12, 31)
    else:
        last_day_previous_quarter = datetime.date(
            year, last_month_previous_quarter + 1, 1
        ) - datetime.timedelta(days=1)

    return {
        "previous_quarter_start": first_day_previous_quarter.strftime("%B %d, %Y"),
        "previous_quarter_end": last_day_previous_quarter.strftime("%B %d, %Y"),
        "previous_quarter": f"Quarter {previous_quarter}, {year}",
    }


def month_dates():
    previous_month_end = datetime.date.today().replace(day=1) - datetime.timedelta(
        days=1
    )
    return {
        "previous_month": previous_month_end.strftime("%B, %Y"),
        "previous_month_start": previous_month_end.replace(day=1).strftime("%B %d, %Y"),
        "previous_month_end": previous_month_end.strftime("%B %d, %Y"),
    }


def date_strings():
    return quarterly_dates() | month_dates() | yearly_dates() | fiscal_year_dates()


@click.command()
@click.argument("filenames", nargs=-1, type=click.Path(exists=True))
@click.option("--yes", "-y", is_flag=True, help="Automatically confirm submissions.")
@click.option("--no", "-n", is_flag=True, help="Automatically avoid submissions.")
def process_request(filenames, yes, no):
    """
    Process a request file and print its content with formatted dates.
    """
    # Check for conflicting flags
    if yes and no:
        raise click.UsageError(
            "Conflicting options: cannot use both '-y/--yes' and '-n/--no' at the same time."
        )

    for filename in filenames:

        request = frontmatter.load(filename)

        agency_id = request["agency"]

        try:
            agency = client.agency.get(agency_id)
        except ValueError as err:
            if "Not found" in str(err):
                raise click.ClickException(
                    f"Could not find an agency with the id: {request['agency']}."
                )
            else:
                raise click.ClickException(err)

        try:
            title = request["title"].format(**date_strings())
            body = request.content.format(**date_strings())
        except KeyError as err:
            (missing_key,) = err.args
            raise click.ClickException(
                f"Unrecognized variable in your request template: {missing_key}"
            )

        click.echo(f"agency: {agency['name']}")
        click.echo(f" title: {title}")
        click.echo(f"  body: {body}")
        click.echo("")

        try:
            already_submitted = client.foia.filter(title=title, agency_id=agency_id)
        except AssertionError as err:
            raise click.ClickException(err)

        if request["start_date"] and request["start_date"] > datetime.date.today():
            click.echo("It is before this request's template's start date.")
        elif any(
            body in request["communications"][0]["communication"]
            for request in already_submitted
        ):
            click.echo("This request has already been made")

        elif not no and (yes or click.confirm("Shall we submit this FOIA request?")):
            response = client.foia.create(
                title=title,
                document_request=body,
                agency_ids=[agency_id],
                organization=request["muckrock_organization"],
            )
            if response["status"] == "FOI Request submitted":
                click.echo(f"Submitted: https://www.muckrock.com{response['Location']}")


if __name__ == "__main__":
    process_request()
