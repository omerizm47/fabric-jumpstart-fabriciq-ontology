@echo off
cd /d C:\Users\omerguzel\fabric-jumpstart-fabriciq-ontology
for %%A in (
    "construction ee8a5d4d-9d33-4d11-9997-7f91af878bbd"
    "education 61b4d577-724e-4258-bee4-c64f10b0fc93"
    "energy-grid 74aba7db-7ea5-4bfd-93b3-a01fe3716139"
    "financial-services 9bd7af9c-2c24-49b7-812c-a84dd37e2b25"
    "hospitality 7235ab18-0ba4-441e-b633-bc57f9e82ffa"
    "manufacturing-qc 8b535fae-cd55-4e17-a328-f2628de90cb2"
    "media ac507877-0899-4e34-be43-9306be4eff66"
    "professional-services 6b759b32-548c-47d3-ac32-f16aeb34eb1e"
    "retail-sales 7d82bcd4-0a36-4b7b-954f-00a0deff0427"
    "transportation 362181f4-0101-4319-96f1-7a8802121645"
) do (
    for /f "tokens=1,2" %%B in (%%A) do (
        echo === promoting %%B ===
        python _promote_native.py %%B %%C || exit /b 1
    )
)
echo ALL PROMOTED
