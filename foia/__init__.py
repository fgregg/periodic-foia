import datetime
import os
import sys

import click
import frontmatter
import muckrock

# Initialize MuckRock client
client = muckrock.MuckRock(token=os.getenv("MUCKROCK_API_KEY"))


def date_strings():
    previous_month_end = datetime.date.today().replace(day=1) - datetime.timedelta(
        days=1
    )
    previous_month = previous_month_end.strftime("%B, %Y")
    previous_month_start = previous_month_end.replace(day=1).strftime("%B %d, %Y")
    previous_month_end = previous_month_end.strftime("%B %d, %Y")
    return {
        "previous_month": previous_month,
        "previous_month_start": previous_month_start,
        "previous_month_end": previous_month_end,
    }


@click.command()
@click.argument("filename", type=click.Path(exists=True))
def process_request(filename):
    """
    Process a request file and print its content with formatted dates.
    """
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

    try:
        already_submitted = client.foia.filter(title=title, agency_id=agency_id)
    except AssertionError as err:
        raise click.ClickException(err)

    if any(
        body in request["communications"][0]["communication"]
        for request in already_submitted
    ):
        click.echo("This request has already been made")
        sys.exit(1)

    if click.confirm("Shall we submit this FOIA request?"):
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
