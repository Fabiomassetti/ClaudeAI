def sql_life_pension_withdrawals(ramo, nome_view="", excluidos=False):
    aux_query = ""
    # faz query nas tabelas:
    if nome_view:
        aux_query = f"inner join {nome_view} dif on dif.pid = pol.pensionIdentification"

    query = f"""
        select pensionIdentification || nvl('.[' || date_format(max(liquidationDate), 'yyyy-MM-dd') || ']', '') as id,
            pensionIdentification as certificateId,
            true as withdrawalOccurence,
            type,
            nvl(concat(date_format(requestDate, 'yyyy-MM-dd'), 'T00:00:00Z'), '') as requestDate,
            named_struct(
                "amount", format_number(sum(amount), '#.##'),
                "unitType", "MONETARIO",
                "unit", named_struct(
                    "code", code,
                    "description", description
                )
            ) as amount,
            nvl(concat(date_format(max(liquidationDate), 'yyyy-MM-dd'), 'T00:00:00Z'), '') as liquidationDate,
            named_struct(
                "amount", format_number(sum(ChargedAmount), '#.##'),
                "unitType", "MONETARIO",
                "unit", named_struct(
                    "code", code_charge,
                    "description", desc_charge
                )
            ) as postedChargedAmount,
            nature,
            collect_set(
                named_struct(
                    "FIECNPJ", FIECNPJ,
                    "FIEName", FIEName,
                    "FIETradeName", FIETradeName
                )
            ) as FIE
        from kiprev_gold.opin_life_pension_resgates pol
        {aux_query}
        where type != '' and {"" if excluidos else "not"}(pol.is_removed <=> 'S')
        group by pensionIdentification,
                liquidationDate,
                type,
                requestDate,
                nature,
                code,
                description,
                code_charge,
                desc_charge
        union all
        select pensionIdentification as id,
            pensionIdentification as certificateId,
            false as withdrawalOccurence,
            type,
            '' as requestDate,
            null as amount,
            '' as liquidationDate,
            null as postedChargedAmount,
            nature,
            array() as FIE
        from kiprev_gold.opin_life_pension_resgates pol
        {aux_query}
        where type = '' and {"" if excluidos else "not"}(pol.is_removed <=> 'S')
    """

    return query
