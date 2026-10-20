"""Command line entry point: `competitor-tech-stack-audit DOMAIN [DOMAIN ...]`."""
import time
from pathlib import Path

import click

from . import __version__, core
from .benchmark import STATS
from .report import Report, write_excel


@click.command()
@click.argument("domains", nargs=-1, required=True)
@click.option("--pagespeed", is_flag=True, help="Also fetch Google PageSpeed Insights mobile scores (slower).")
@click.option("--psi-key", envvar="PSI_API_KEY", default=None,
              help="Optional PageSpeed API key (or env PSI_API_KEY) for higher rate limits.")
@click.option("--delay", default=1.0, show_default=True, help="Seconds between domains.")
@click.option("-o", "--output", default="tech_stack_audit", show_default=True,
              help="Report name; writes <name>.html and <name>.xlsx")
@click.version_option(__version__)
def main(domains, pagespeed, psi_key, delay, output):
    """Compare the technical SEO setup of DOMAINS side by side (put your own domain first).

    Built by Meer Hamza - linkedin.com/in/meerhamza-seo
    """
    rows = []
    for i, domain in enumerate(domains):
        click.echo(f"[{i + 1}/{len(domains)}] {domain}")
        rows.append(core.audit_domain(domain, psi=pagespeed, psi_key=psi_key))
        if delay and i < len(domains) - 1:
            time.sleep(delay)
    reachable = [r for r in rows if r.get("status") != "unreachable"]
    if not reachable:
        raise click.ClickException("no domain could be reached")

    card = core.scorecard(reachable)
    me = reachable[0]["domain"]
    score_row = card.iloc[-1]
    report = Report(title="Technical SEO comparison", subtitle=" vs ".join(r["domain"] for r in reachable),
                    tool="competitor-tech-stack-audit")
    report.add_cards([(f"{d} (you)" if d == me else d, score_row[d]) for d in card.columns[1:]])
    report.add_benchmark(STATS[0], how_used="The scorecard checks the technical factors this data says still "
                                            "matter for AI search: HTTPS, mobile, speed, sitemaps, structured data.")
    report.add_benchmark(STATS[1], how_used="Structured data and Organization schema are scored separately, and "
                                            "llms.txt plus AI-crawler access are shown for every site.")
    report.add_table("Scorecard", card, note=f"First column is you ({me}).", sheet="Scorecard")
    report.add_table("AI crawler access (robots.txt)", core.ai_table(reachable),
                     note="Blocked = robots.txt disallows the homepage for that crawler.", sheet="AI crawlers")
    report.add_table("Everything collected", core.matrix(reachable), sheet="Details")
    notes = {r.get("psi_note") for r in reachable} - {None, "ok"}
    if notes:
        click.echo("PageSpeed: " + "; ".join(sorted(notes)))
        report.add_text("PageSpeed Insights", sorted(notes))
    if len(reachable) < len(rows):
        report.add_text("Not reachable", [r["domain"] for r in rows if r.get("status") == "unreachable"])

    html_path = report.save_html(Path(output).with_suffix(".html"))
    xlsx_path = write_excel(report.sheets, Path(output).with_suffix(".xlsx"))
    click.secho(f"Report: {html_path}\nData:   {xlsx_path}", fg="green", bold=True)
    console = card.replace({"✅": "yes", "❌": "no"})  # Windows consoles can't print emoji
    click.echo(console.to_string(index=False))


if __name__ == "__main__":
    main()
