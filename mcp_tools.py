# ============================================
# arya/mcp_tools.py
# ARYA MCP Tools Server
# Run separately: python mcp_tools.py
# ⚠️ Verify this against your Hours 32-33 MCP setup before relying on it —
# the mcp Python SDK's API (Server class location, ListToolsResult, etc.)
# has changed across versions. If this throws an import or class error,
# paste the traceback and we'll match it to your installed mcp version.
# ============================================

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult, ListToolsResult
import asyncio, math, sys
from datetime import datetime, timedelta

app = Server("arya-tools-server")

print("ARYA Tools MCP Server starting...", file=sys.stderr)


@app.list_tools()
async def list_tools() -> ListToolsResult:
    return ListToolsResult(tools=[

        Tool(
            name="calculator",
            description="Evaluate mathematical expressions accurately. Use for any calculation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression. Example: 85000 * 0.15 or (120000 - 85000) / 85000 * 100"
                    }
                },
                "required": ["expression"]
            }
        ),

        Tool(
            name="unit_converter",
            description="Convert between units — currency (rough), distance, weight, temperature.",
            inputSchema={
                "type": "object",
                "properties": {
                    "value":     {"type": "number"},
                    "from_unit": {"type": "string", "description": "e.g. USD, km, kg, celsius"},
                    "to_unit":   {"type": "string", "description": "e.g. PKR, miles, lbs, fahrenheit"}
                },
                "required": ["value", "from_unit", "to_unit"]
            }
        ),

        Tool(
            name="date_utilities",
            description="Date calculations — days between dates, add/subtract days, day of week.",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "description": "today | days_between | add_days | day_of_week"},
                    "date1": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "date2": {"type": "string", "description": "Second date for days_between"},
                    "days":  {"type": "integer", "description": "Days to add/subtract"}
                },
                "required": ["operation"]
            }
        ),

        Tool(
            name="text_stats",
            description="Count words, characters, sentences, and estimate reading time.",
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string", "description": "Text to analyze"}},
                "required": ["text"]
            }
        ),

        Tool(
            name="quick_summary",
            description="Summarize a long text to 3-5 key bullet points.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text":        {"type": "string"},
                    "max_bullets": {"type": "integer", "description": "Max bullet points. Default: 4"}
                },
                "required": ["text"]
            }
        ),
    ])


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:

    if name == "calculator":
        expr = arguments.get("expression", "")
        try:
            allowed = set("0123456789+-*/.()% ")
            clean   = "".join(c for c in expr if c in allowed)
            if not clean:
                result = "Error: no valid expression found"
            else:
                val    = eval(clean, {"__builtins__": {}}, {"math": math})
                result = f"= {round(val, 6):,}" if isinstance(val, float) else f"= {val:,}"
        except Exception as e:
            result = f"Calculation error: {e}"
        return CallToolResult(content=[TextContent(type="text", text=result)])

    elif name == "unit_converter":
        value     = arguments.get("value", 0)
        from_unit = arguments.get("from_unit", "").lower()
        to_unit   = arguments.get("to_unit", "").lower()

        conversions = {
            ("usd", "pkr"): 280, ("pkr", "usd"): 1/280,
            ("eur", "pkr"): 305, ("gbp", "pkr"): 355,
            ("km", "miles"): 0.621371, ("miles", "km"): 1.60934,
            ("kg", "lbs"): 2.20462, ("lbs", "kg"): 0.453592,
            ("km", "meters"): 1000, ("meters", "km"): 0.001,
        }

        key = (from_unit, to_unit)

        if key in conversions:
            converted = value * conversions[key]
            result = f"{value} {from_unit} = {converted:,.2f} {to_unit}"
        elif from_unit == "celsius" and to_unit in ["fahrenheit", "f"]:
            result = f"{value}°C = {(value * 9/5) + 32:.1f}°F"
        elif from_unit in ["fahrenheit", "f"] and to_unit == "celsius":
            result = f"{value}°F = {(value - 32) * 5/9:.1f}°C"
        else:
            result = f"Conversion {from_unit} → {to_unit} not supported. Supported: {list(conversions.keys())}"

        return CallToolResult(content=[TextContent(type="text", text=result)])

    elif name == "date_utilities":
        operation = arguments.get("operation", "today")
        try:
            if operation == "today":
                result = f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
            elif operation == "days_between":
                d1 = datetime.strptime(arguments["date1"], "%Y-%m-%d")
                d2 = datetime.strptime(arguments["date2"], "%Y-%m-%d")
                result = f"Days between {arguments['date1']} and {arguments['date2']}: {abs((d2 - d1).days)} days"
            elif operation == "add_days":
                d1 = datetime.strptime(arguments.get("date1", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
                days = arguments.get("days", 0)
                new_date = d1 + timedelta(days=days)
                result = f"{d1.strftime('%Y-%m-%d')} + {days} days = {new_date.strftime('%A, %B %d, %Y')}"
            elif operation == "day_of_week":
                d1 = datetime.strptime(arguments["date1"], "%Y-%m-%d")
                result = f"{arguments['date1']} is a {d1.strftime('%A')}"
            else:
                result = f"Unknown operation: {operation}"
        except Exception as e:
            result = f"Date error: {e}"

        return CallToolResult(content=[TextContent(type="text", text=result)])

    elif name == "text_stats":
        text      = arguments.get("text", "")
        words     = len(text.split())
        chars     = len(text)
        chars_ns  = len(text.replace(" ", ""))
        sentences = len([s for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()])
        read_min  = round(words / 200, 1)

        result = (f"Words: {words} | Characters: {chars} ({chars_ns} without spaces) | "
                  f"Sentences: {sentences} | Reading time: ~{read_min} minutes")
        return CallToolResult(content=[TextContent(type="text", text=result)])

    elif name == "quick_summary":
        text        = arguments.get("text", "")
        max_bullets = arguments.get("max_bullets", 4)

        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 20]

        if not sentences:
            return CallToolResult(content=[TextContent(type="text", text="Text too short to summarize.")])

        step     = max(1, len(sentences) // max_bullets)
        selected = [sentences[i] for i in range(0, min(len(sentences), step * max_bullets), step)]
        bullets  = "\n".join([f"• {s}." for s in selected[:max_bullets]])

        return CallToolResult(content=[TextContent(type="text", text=bullets)])

    return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")])


async def main():
    print("ARYA Tools Server ready.", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())