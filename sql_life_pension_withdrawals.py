def sql_life_pension_withdrawals(ramo, nome_view="", excluidos=False):
    aux_query = ""
    if nome_view:
        aux_query = f"inner join {nome_view} dif on dif.pid = pol.pensionIdentification"

    filtro_removed = "" if excluidos else "not"

    query = f"""
        with withdrawals_agg as (
            select
                pensionIdentification,
                type,
                nvl(concat(date_format(requestDate, 'yyyy-MM-dd'), 'T00:00:00Z'), '') as requestDate,
                named_struct(
                    "amount",           format_number(sum(amount), '#.##'),
                    "unitType",         "MONETARIO",
                    "unit",             named_struct(
                                            "code",        code,
                                            "description", description
                                        )
                ) as amount,
                nvl(concat(date_format(max(liquidationDate), 'yyyy-MM-dd'), 'T00:00:00Z'), '') as liquidationDate,
                named_struct(
                    "amount",           format_number(sum(ChargedAmount), '#.##'),
                    "unitType",         "MONETARIO",
                    "unit",             named_struct(
                                            "code",        code_charge,
                                            "description", desc_charge
                                        )
                ) as postedChargedAmount,
                nature,
                FIECNPJ,
                FIEName,
                FIETradeName
            from kiprev_gold.opin_life_pension_resgates pol
            {aux_query}
            where type != '' and {filtro_removed}(pol.is_removed <=> 'S')
            group by
                pensionIdentification,
                type,
                requestDate,
                nature,
                code,
                description,
                code_charge,
                desc_charge,
                FIECNPJ,
                FIEName,
                FIETradeName
        )
        select
            pensionIdentification || nvl('.[' || substr(max(liquidationDate), 1, 10) || ']', '') as id,
            pensionIdentification as certificateId,
            true as withdrawalOccurence,
            collect_list(
                named_struct(
                    "type",                 type,
                    "requestDate",          requestDate,
                    "amount",               amount,
                    "liquidationDate",      liquidationDate,
                    "postedChargedAmount",  postedChargedAmount
                )
            ) as withdrawalInfo,
            nature,
            collect_set(
                named_struct(
                    "FIECNPJ",      FIECNPJ,
                    "FIEName",      FIEName,
                    "FIETradeName", FIETradeName
                )
            ) as FIE
        from withdrawals_agg
        group by
            pensionIdentification,
            nature

        union all

        select
            pensionIdentification as id,
            pensionIdentification as certificateId,
            false as withdrawalOccurence,
            array() as withdrawalInfo,
            nature,
            array() as FIE
        from kiprev_gold.opin_life_pension_resgates pol
        {aux_query}
        where type = '' and {filtro_removed}(pol.is_removed <=> 'S')
    """

    return query
