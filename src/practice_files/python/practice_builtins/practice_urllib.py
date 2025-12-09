from urllib.parse import unquote


def main():
    ss = "jth6e5_revenue_events%2Cjth6e5_revenue_per_event%2Cc8ces6_revenue_events%2Cc8ces6_revenue_per_event%2C769f6z_revenue_events%2C769f6z_revenue_per_event"

    # jth6e5_revenue_events,jth6e5_revenue_per_event,c8ces6_revenue_events,c8ces6_revenue_per_event,769f6z_revenue_events,769f6z_revenue_per_event
    print(unquote(ss))


if __name__ == "__main__":
    main()
